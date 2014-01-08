#!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse


class Facter(object):
    unit = 'value'

    def __init__(self, reviewer):
        self.reviewer = reviewer

    @classmethod
    def get_fact_definitions(cls):
        raise NotImplementedError

    @property
    def page_uuid(self):
        return self.reviewer.page_uuid

    @property
    def page_url(self):
        return self.reviewer.page_url

    @property
    def review(self):
        return self.reviewer.review_dao

    @property
    def config(self):
        return self.reviewer.config

    def get(self, url):
        return self.reviewer._get(url)

    def add_fact(self, key, value):
        self.reviewer.add_fact(key, value)

    def add_violation(self, key, value):
        self.reviewer.add_violation(key, value)

    def async_get(self, url, handler, method='GET', **kw):
        self.reviewer._async_get(url, handler, method, **kw)

    def is_valid(self, url):
        try:
            return urlparse.urlparse(url)
        except ValueError:
            return None

    def is_absolute(self, url):
        return bool(urlparse.urlparse(url).scheme)

    def rebase(self, url):
        return urlparse.urljoin(self.page_url.rstrip('/'), url)

    def to_gzip(self, content):
        return content.encode('zip')
