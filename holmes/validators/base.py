#!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse


class Validator(object):
    def __init__(self, reviewer):
        self.reviewer = reviewer
        self.url_buffer = set()

    @classmethod
    def get_violation_definitions(cls):
        raise NotImplementedError

    def is_absolute(self, url):
        return bool(urlparse.urlparse(url).scheme)

    def rebase(self, url):
        return urlparse.urljoin(self.page_url.rstrip('/'), url)

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

    def validate(self):
        return True

    def to_gzip(self, content):
        return content.encode('zip')

    def enqueue(self, url):
        self.reviewer.enqueue(url)

    def add_fact(self, key, value):
        self.reviewer.add_fact(key, value)

    def add_violation(self, key, value, points):
        self.reviewer.add_violation(key, value, points)

    def is_valid(self, url):
        try:
            return urlparse.urlparse(url)
        except ValueError:
            return None

    def test_url(self, url, response, broken_link_callback=None, moved_link_callback=None):
        status = response.status_code

        if status > 399:
            if broken_link_callback:
                broken_link_callback(url, response)
            return False

        if status == 302 or status == 307:
            if moved_link_callback:
                moved_link_callback(url, response)
            return False

        if response.url.rstrip('/') != url.rstrip('/'):
            return False

        return True

    def send_url(self, url, response):
        if self.test_url(url, response, self.broken_link_violation, self.moved_link_violation):
            self.url_buffer.add(url)

        if len(self.url_buffer) > self.config.MAX_ENQUEUE_BUFFER_LENGTH:
            self.flush()

    def flush(self):
        if not self.url_buffer:
            return

        self.enqueue(self.url_buffer)
        self.url_buffer = set()

    def broken_link_violation(self):
        raise NotImplementedError('broken_link_violation method need to be implemented by {0}'.format(self.__class__.__name__))

    def moved_link_violation(self):
        raise NotImplementedError('moved_link_violation method need to be implemented by {0}'.format(self.__class__.__name__))
