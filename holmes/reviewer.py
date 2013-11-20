#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from os.path import join
import inspect

import requests
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError, InvalidSchema
import lxml.html
import logging
from ujson import dumps

from holmes.config import Config
from holmes.facters import Facter
from holmes.validators.base import Validator


class InvalidReviewError(RuntimeError):
    pass


class ReviewDAO(object):
    def __init__(self, page_uuid, page_url):
        self.page_uuid = page_uuid
        self.page_url = page_url
        self.facts = {}
        self.violations = []
        self.data = {}
        self._current = None

    def add_fact(self, key, title, value, unit=None):
        self.facts[key] = {
            'key': key,
            'value': value,
            'title': title,
            'unit': unit
        }

    def add_violation(self, key, title, description, points):
        self.violations.append({
            'key': key,
            'title': title,
            'description': description,
            'points': points
        })

    def to_dict(self):
        return {
            'page_uuid': self.page_uuid,
            'page_url': self.page_url,
            'facts': self.facts.values(),
            'violations': self.violations
        }


class Reviewer(object):
    def __init__(self, api_url, page_uuid, page_url, config=None, validators=[], facters=[], async_get=None, wait=None, wait_timeout=None):
        self.api_url = api_url

        self.page_uuid = page_uuid
        self.page_url = page_url

        self.review_dao = ReviewDAO(self.page_uuid, self.page_url)

        assert isinstance(config, Config), 'config argument must be an instance of holmes.config.Config'
        self.config = config

        for facter in facters:
            message = 'All facters must subclass holmes.facters.Facter (Error: %s)' % facter.__class__.__name__
            assert inspect.isclass(facter), message
            assert issubclass(facter, Facter), message

        for validator in validators:
            message = 'All validators must subclass holmes.validators.base.Validator (Error: %s)' % validator.__class__.__name__
            assert inspect.isclass(validator), message
            assert issubclass(validator, Validator), message

        self.validators = validators
        self.facters = facters

        self.responses = {}
        self.raw_responses = {}
        self.status_codes = {}

        self.proxies = None
        if self.config.HTTP_PROXY_HOST is not None:
            proxy = "%s:%s" % (self.config.HTTP_PROXY_HOST, self.config.HTTP_PROXY_PORT)
            http_proxy = proxy
            https_proxy = proxy

            self.proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }

        self.async_get_func = async_get
        self._wait_for_async_requests = wait
        self._wait_timeout = wait_timeout

    def _async_get(self, url, handler, method='GET', **kw):
        if self.async_get_func:
            self.async_get_func(url, handler, method, **kw)

    def _get(self, url):
        if self.proxies:
            logging.debug('Getting "%s" using proxy "%s:%s"...' % self.proxies.get('http', None))
            return requests.get(url, proxies=self.proxies)

        return requests.get(url)

    def _post(self, url, data):
        if self.proxies:
            logging.debug('Posting to "%s" using proxy "%s:%s"...' % self.proxies.get('http', None))
            return requests.post(url, data=data, proxies=self.proxies)

        return requests.post(url, data=data)

    def review(self):
        self.load_content(self.content_loaded)
        self.wait_for_async_requests()

    def load_content(self, callback):
        self._async_get(self.page_url, callback)

    def content_loaded(self, url, response):
        if response.status_code > 399:
            logging.error("Could not load '%s' (%s)!" % (url, response.status_code))
            return

        self._current = response

        try:
            self._current.html = lxml.html.fromstring(response.text)
        except (lxml.etree.XMLSyntaxError, lxml.etree.ParserError):
            self._current.html = None

            self.add_violation(
                key='invalid.content',
                title='Invalid Content',
                description='Fail to parse content from %s' % url,
                points=1000)

        self.run_facters()
        self.wait_for_async_requests()

        self.run_validators()
        self.wait_for_async_requests()

        self.save_review()

    @property
    def current(self):
        return self._current

    def get_response(self, url):
        if url in self.responses:
            return self.responses[url]

        self.responses[url] = {}

        try:
            response = self._get(url)
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
        if not hasattr(self.current, 'html') or self.current.html is None:
            return lxml.html.HtmlElement()
        else:
            return self.current.html

    def get_status_code(self, url):
        if not url in self.status_codes:
            try:
                response = requests.request(method='GET', url=url, stream=True, timeout=10.0, proxies=self.proxies)
                response.iter_lines().next()
                self.raw_responses[url] = response
                self.status_codes[url] = response.status_code
            except (TooManyRedirects, Timeout, HTTPError, ConnectionError, InvalidSchema):
                err = sys.exc_info()[1]
                logging.warn('ERROR IN %s: %s' % (url, str(err)))
                self.status_codes[url] = 404

        return self.status_codes[url]

    def run_facters(self):
        for facter in self.facters:
            logging.debug('---------- Started running facter %s ---------' % facter.__name__)
            facter_instance = facter(self)
            facter_instance.get_facts()

    def run_validators(self):
        for validator in self.validators:
            logging.debug('---------- Started running validator %s ---------' % validator.__name__)
            validator_instance = validator(self)
            validator_instance.validate()

    def get_url(self, url):
        return join(self.api_url.rstrip('/'), url.lstrip('/'))

    def enqueue(self, *urls):
        if not urls:
            return

        if len(urls) == 1:
            post_url = self.get_url('/page')
            data = dumps({
                'url': urls[0],
                'origin_uuid': str(self.page_uuid)
            })
            error_message = "Could not enqueue page '" + urls[0] + "'! Status Code: %d, Error: %s"
        else:
            post_url = self.get_url('/pages')
            data = {
                "url": urls,
                'origin_uuid': str(self.page_uuid)
            }
            error_message = "Could not enqueue the " + str(len(urls)) + " pages sent! Status Code: %d, Error: %s"

        response = self._post(post_url, data=data)

        if response.status_code > 399:
            logging.error(error_message % (
                response.status_code,
                response.text
            ))

    def add_fact(self, key, value, title, unit='value'):
        self.review_dao.add_fact(key, title, value, unit)

    def add_violation(self, key, title, description, points):
        self.review_dao.add_violation(key, title, description, points)

    def save_review(self):
        url = self.get_url('/page/%s/review/' % (self.page_uuid))

        try:
            data = dumps(self.review_dao.to_dict())
            response = self._post(url, data={
                'review': data
            })
        except ConnectionError:
            err = sys.exc_info()[1]
            logging.error("Could not save review! ConnectionError - %s (%s)" % (
                url,
                str(err)
            ))

        if response.status_code > 399:
            logging.error("Could not save review! Status Code: %d, Error: %s" % (
                response.status_code,
                response.text
            ))

    def wait_for_async_requests(self):
        self._wait_for_async_requests(self._wait_timeout)
