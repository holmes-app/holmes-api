#!/usr/bin/python
# -*- coding: utf-8 -*-

import StringIO
import gzip


class Validator(object):
    def __init__(self, reviewer):
        self.reviewer = reviewer

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

    def to_gzip(self, content):
        try:
            content = content.encode('utf-8')
        except UnicodeEncodeError:
            pass

        out = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=out, mode='w')
        f.write(content)
        f.close()

        return out.getvalue()

    def enqueue(self, *url):
        self.reviewer.enqueue(*url)

    def add_fact(self, key, value, unit='value'):
        self.reviewer.add_fact(key, value, unit)

    def add_violation(self, key, title, description, points):
        self.reviewer.add_violation(key, title, description, points)
