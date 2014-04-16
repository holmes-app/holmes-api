#!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse
from holmes.utils import is_valid


class Baser(object):

    def __init__(self, reviewer):
        self.reviewer = reviewer

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

    def is_absolute(self, url):
        return bool(urlparse.urlparse(url).scheme)

    def rebase(self, url):
        return urlparse.urljoin(self.page_url, url)

    def normalize_url(self, url):
        parse = is_valid(url)
        if parse:
            if not self.is_absolute(url):
                url = self.rebase(url)
            return url
        return None

    def to_gzip(self, content):
        return content.encode('zip')

    def add_fact(self, key, value):
        self.reviewer.add_fact(key, value)

    def async_get(self, url, handler, method='GET', **kw):
        self.reviewer._async_get(url, handler, method, **kw)


class Facter(Baser):

    unit = 'value'

    @classmethod
    def get_fact_definitions(cls):
        raise NotImplementedError

    def add_violation(self, key, value):
        self.reviewer.add_violation(key, value)
