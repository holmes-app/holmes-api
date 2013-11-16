#!/usr/bin/python
# -*- coding: utf-8 -*-


class Facter(object):
    def __init__(self, reviewer):
        self.reviewer = reviewer

    @property
    def page_uuid(self):
        return self.reviewer.page_uuid

    @property
    def page_url(self):
        return self.reviewer.page_url

    @property
    def config(self):
        return self.reviewer.config

    def get(self, url):
        return self.reviewer._get(url)

    def get_async(self, url, handler):
        return self.reviewer._get_async(url)

    def add_fact(self, key, value, title, unit='value'):
        self.reviewer.add_fact(key, value, title, unit)

    def add_violation(self, key, title, description, points):
        self.reviewer.add_violation(key, title, description, points)
