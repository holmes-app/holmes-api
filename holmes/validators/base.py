#!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse


class Validator(object):
    def __init__(self, reviewer):
        self.reviewer = reviewer

    def is_absolute(self, url):
        return bool(urlparse.urlparse(url).scheme)

    def rebase(self, url):
        return urlparse.urljoin(self.page_url.rstrip('/'), url.lstrip('/'))

    @property
    def page_uuid(self):
        return self.reviewer.page_uuid

    @property
    def page_url(self):
        return self.reviewer.page_url

    @property
    def review_uuid(self):
        return self.reviewer.review_uuid

    @property
    def config(self):
        return self.reviewer.config

    def validate(self):
        return True

    def get_response(self, url):
        return self.reviewer.get_response(url)

    def get_raw_response(self, url):
        return self.reviewer.raw_responses.get(url, None)

    def get_status_code(self, url):
        return self.reviewer.get_status_code(url)

    def to_gzip(self, content):
        return content.encode('zip')

    def enqueue(self, *url):
        self.reviewer.enqueue(*url)

    def add_fact(self, key, value, title, unit='value'):
        self.reviewer.add_fact(key, value, title, unit)

    def add_violation(self, key, title, description, points):
        self.reviewer.add_violation(key, title, description, points)
