#!/usr/bin/python
# -*- coding: utf-8 -*-


class Validator(object):
    def __init__(self, reviewer, review):
        self.reviewer = reviewer
        self.review = review

    def validate(self):
        return True

    def add_fact(self, key, value, unit='value'):
        self.review.add_fact(key, value, unit)
