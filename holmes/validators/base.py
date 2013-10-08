#!/usr/bin/python
# -*- coding: utf-8 -*-

import StringIO
import gzip


class Validator(object):
    def __init__(self, reviewer):
        self.reviewer = reviewer

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

    def add_fact(self, key, value, unit='value'):
        self.reviewer.add_fact(key, value, unit)

    def add_violation(self, key, title, description, points):
        self.reviewer.add_violation(key, title, description, points)
