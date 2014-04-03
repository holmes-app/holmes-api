#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class BodyValidator(Validator):
    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.body.not_found': {
                'title': 'Page body not found',
                'description': lambda value: 'Body was not found on %s.' % value,
                'category': 'Semantics'
            }
        }

    def validate(self):
        body = self.get_body()

        if not body:

            page_url = self.reviewer.page_url

            self.add_violation(
                key='page.body.not_found',
                value=page_url,
                points=50
            )

    def get_body(self):
        return self.review.data.get('page.body', None)
