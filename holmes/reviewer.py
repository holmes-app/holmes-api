#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.models import Review


class Reviewer(object):
    def __init__(self, page):
        self.page = page

    def review(self):
        new_review = Review(page=self.page)

        return new_review
