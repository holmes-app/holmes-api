#!/usr/bin/python
# -*- coding: utf-8 -*-


class Validator(object):
    def __init__(self, reviewer, review):
        self.reviewer = reviewer
        self.review = review

    def validate(self):
        return True
