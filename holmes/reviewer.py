#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import join
from uuid import UUID
import inspect

import requests
import lxml.html

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

        assert isinstance(config, Config), "config argument must be an instance of holmes.config.Config"
        self.config = config

        for validator in validators:
            assert inspect.isclass(validator), "All validators must subclass holmes.validators.base.Validator"
            assert issubclass(validator, Validator), "All validators must subclass holmes.validators.base.Validator"

        self.validators = validators

        self.responses = {}

    def review(self):
        self.load_content()
        self.run_validators()

    def load_content(self):
        self.get_response(self.page_url)

        if self.responses[self.page_url]['status'] > 399:
            raise InvalidReviewError("Could not load '%s'!" % self.page_url)

    def get_response(self, url):
        if url in self.responses:
            return

        response = requests.get(url)

        self.responses[url] = {}
        self.responses[url]['status'] = response.status_code
        self.responses[url]['content'] = response.text

        self.responses[url]['html'] = None
        if response.status_code < 399:
            self.responses[url]['html'] = lxml.html.fromstring(response.text)

    def run_validators(self):
        for validator in self.validators:
            validator_instance = validator(self)
            validator_instance.validate()

    def get_url(self, url):
        return join(self.api_url.rstrip('/'), url.lstrip('/'))

    def add_fact(self, key, value, unit='value'):
        url = self.get_url('/page/%s/review/%s/fact' % (self.page_uuid, self.review_uuid))
        response = requests.post(url, data={
            "key": key,
            "value": value,
            "unit": unit
        })

        if response.status_code > 399:
            raise InvalidReviewError("Could not add fact '%s' to review %s! Status Code: %d, Error: %s" % (
                key,
                self.review_uuid,
                response.status_code,
                response.text
            ))

    def add_violation(self, key, title, description, points):
        url = self.get_url('/page/%s/review/%s/violation' % (self.page_uuid, self.review_uuid))
        response = requests.post(url, data={
            "key": key,
            "title": title,
            "description": description,
            "points": points
        })

        if response.status_code > 399:
            raise InvalidReviewError("Could not add violation '%s' to review %s! Status Code: %d, Error: %s" % (
                key,
                self.review_uuid,
                response.status_code,
                response.text
            ))

    def complete(self):
        url = self.get_url('/page/%s/review/%s/complete' % (self.page_uuid, self.review_uuid))
        response = requests.post(url, data={})

        if response.status_code > 399:
            raise InvalidReviewError("Could not complete review %s! Status Code: %d, Error: %s" % (
                self.review_uuid,
                response.status_code,
                response.text
            ))
