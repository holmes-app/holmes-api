#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class LastModifiedValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.last_modified.not_found': {
                'title': 'Last-Modified not found',
                'description': lambda value: 'Last-Modified was not found on %s.' % value,
                'category': 'HTTP',
                'generic_description': (
                    'The Last-Modified Header information allows Web Crawlers '
                    '(like Holmes) and search engines to know if the page is '
                    'modified since the last content retrival. If Last-Modified '
                    'wasn\'t present, all requests made by this engines on the '
                    'page will proccess all the content and can be '
                    'performatically bad to the server.'
                )
            }
        }

    def validate(self):
        last_modified = self.get_last_modified()

        if not last_modified:
            page_url = self.reviewer.page_url

            self.add_violation(
                key='page.last_modified.not_found',
                value=page_url,
                points=50
            )

    def get_last_modified(self):
        return self.review.data.get('page.last_modified', None)
