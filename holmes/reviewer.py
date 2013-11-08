#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from os.path import join
from uuid import UUID
import inspect

import requests
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError, InvalidSchema
import lxml.html
import logging

from holmes.config import Config
from holmes.validators.base import Validator


class InvalidReviewError(RuntimeError):
    pass


class Reviewer(object):
    def __init__(self, api_url, page_uuid, page_url, review_uuid, config=None, validators=[]):
        self.api_url = api_url

        self.page_uuid = page_uuid
        if not isinstance(self.page_uuid, UUID):
            self.page_uuid = UUID(page_uuid)

        self.page_url = page_url
        self.review_uuid = review_uuid
        if not isinstance(self.review_uuid, UUID):
            self.review_uuid = UUID(review_uuid)

        assert isinstance(config, Config), 'config argument must be an instance of holmes.config.Config'
        self.config = config

        for validator in validators:
            assert inspect.isclass(validator), 'All validators must subclass holmes.validators.base.Validator'
            assert issubclass(validator, Validator), 'All validators must subclass holmes.validators.base.Validator'

        self.validators = validators

        self.responses = {}
        self.raw_responses = {}
        self.status_codes = {}

    def review(self):
        self.load_content()
        self.run_validators()
        self.complete()

    def load_content(self):
        self.get_response(self.page_url)

        if self.responses[self.page_url]['status'] > 399:
            raise InvalidReviewError("Could not load '%s'!" % self.page_url)

    @property
    def current(self):
        if not self.page_url in self.responses:
            self.load_content()

        return self.responses[self.page_url]

    def get_response(self, url):
        if url in self.responses:
            return self.responses[url]

        self.responses[url] = {}

        try:
            response = requests.get(url)
            self.raw_responses[url] = response
        except Exception:
            result = {
                'url': url,
                'status': 404,
                'content': '',
                'html': None
            }
        else:
            result = {
                'url': url,
                'status': response.status_code,
                'content': response.content,
                'html': None
            }

            if response.status_code < 399:
                try:
                    result['html'] = lxml.html.fromstring(response.text)
                except (lxml.etree.XMLSyntaxError, lxml.etree.ParserError):
                    result['html'] = None

                    self.add_violation(
                        key='invalid.content',
                        title='Invalid Content',
                        description='Fail to parse content from %s' % url,
                        points=1000)

        self.responses[url] = result

        return result

    @property
    def current_html(self):
        if 'html' not in self.current or self.current['html'] is None:
            return lxml.html.HtmlElement()
        else:
            return self.current['html']

    def get_status_code(self, url):
        if not url in self.status_codes:
            try:
                response = requests.request(method='GET', url=url, stream=True, timeout=10.0)
                response.iter_lines().next()
                self.raw_responses[url] = response
                self.status_codes[url] = response.status_code
            except (TooManyRedirects, Timeout, HTTPError, ConnectionError, InvalidSchema):
                err = sys.exc_info()[1]
                logging.warn('ERROR IN %s: %s' % (url, str(err)))
                self.status_codes[url] = 404

        return self.status_codes[url]

    def run_validators(self):
        for validator in self.validators:
            validator_instance = validator(self)
            validator_instance.validate()

    def get_url(self, url):
        return join(self.api_url.rstrip('/'), url.lstrip('/'))

    def enqueue(self, *urls):
        if not urls:
            return

        if len(urls) == 1:
            post_url = self.get_url('/page')
            data = {
                'url': urls[0],
                'origin_uuid': str(self.page_uuid)
            }
            error_message = "Could not enqueue page '" + urls[0] + "'! Status Code: %d, Error: %s"
        else:
            post_url = self.get_url('/pages')
            data = {
                "url": urls,
                'origin_uuid': str(self.page_uuid)
            }
            error_message = "Could not enqueue the " + str(len(urls)) + " pages sent! Status Code: %d, Error: %s"

        response = requests.post(post_url, data=data)

        if response.status_code > 399:
            raise InvalidReviewError(error_message % (
                response.status_code,
                response.text
            ))

    def add_fact(self, key, value, title, unit='value'):
        url = self.get_url('/page/%s/review/%s/fact' % (self.page_uuid, self.review_uuid))

        try:
            response = requests.post(url, data={
                'key': key,
                'value': value,
                'title': title,
                'unit': unit
            })
        except ConnectionError:
            raise InvalidReviewError("Could not add fact '%s' to review %s! ConnectionError - %s" % (
                key,
                self.review_uuid,
                url
                ))

        if response.status_code > 399:
            raise InvalidReviewError("Could not add fact '%s' to review %s! Status Code: %d, Error: %s" % (
                key,
                self.review_uuid,
                response.status_code,
                response.text
            ))

    def add_violation(self, key, title, description, points):
        url = self.get_url('/page/%s/review/%s/violation' % (self.page_uuid, self.review_uuid))

        try:
            response = requests.post(url, data={
                'key': key,
                "title": title,
                "description": description,
                "points": points
            })
        except ConnectionError:
            raise InvalidReviewError("Could not add violation '%s' to review %s! ConnectionError - %s" % (
                key,
                self.review_uuid,
                url
                ))

        if response.status_code > 399:
            raise InvalidReviewError("Could not add violation '%s' to review %s! Status Code: %d, Error: %s" % (
                key,
                self.review_uuid,
                response.status_code,
                response.text
            ))

    def complete(self):
        url = self.get_url('/page/%s/review/%s/complete' % (self.page_uuid, self.review_uuid))

        try:
            response = requests.post(url, data={})
        except ConnectionError:
            raise InvalidReviewError("Could not complete review %s! ConnectionError - %s" % (
                self.review_uuid,
                url
                ))

        if response.status_code > 399:
            raise InvalidReviewError("Could not complete review %s! Status Code: %d, Error: %s" % (
                self.review_uuid,
                response.status_code,
                response.text
            ))
