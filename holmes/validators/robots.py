#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class RobotsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'robots.not_found': {
                'title': 'Robots file not found.',
                'description': lambda value: "The robots file at '%s' was not found." % value
            },
            'robots.empty': {
                'title': 'Robots file was empty.',
                'description': lambda value: "The robots file at '%s' was empty." % value
            }
        }

    def validate(self):
        if not self.reviewer.is_root():
            return

        response = self.review.data['robots.response']

        if response.status_code > 399:
            self.add_violation(
                key='robots.not_found',
                value=response.url,
                points=100
            )
            return

        if not response.text.strip():
            self.add_violation(
                key='robots.empty',
                value=response.url,
                points=100
            )
