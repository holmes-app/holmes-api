#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Baser


class Validator(Baser):

    def __init__(self, reviewer):
        self.reviewer = reviewer
        self.url_buffer = set()

    @classmethod
    def get_violation_definitions(cls):
        raise NotImplementedError

    def add_violation(self, key, value, points):
        self.reviewer.add_violation(key, value, points)

    def validate(self):
        return True

    def enqueue(self, url):
        self.reviewer.enqueue(url)

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

    def send_url(self, url, score, response):
        if self.test_url(url, response, self.broken_link_violation, self.moved_link_violation):
            self.url_buffer.add((url, score))

        if len(self.url_buffer) > self.config.MAX_ENQUEUE_BUFFER_LENGTH:
            self.flush()

    def flush(self):
        if not self.url_buffer:
            return

        self.enqueue(self.url_buffer)
        self.url_buffer = set()

    def broken_link_violation(self):
        text = 'broken_link_violation method need to be implemented by {0}'
        raise NotImplementedError(text.format(self.__class__.__name__))

    def moved_link_violation(self):
        text = 'moved_link_violation method need to be implemented by {0}'
        raise NotImplementedError(text.format(self.__class__.__name__))
