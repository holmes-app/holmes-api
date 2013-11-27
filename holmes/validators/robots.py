#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class RobotsValidator(Validator):
    def validate(self):
        if not self.reviewer.is_root():
            return

        response = self.review.data['robots.response']

        if response.status_code > 399:
            self.add_violation(
                key='robots.not_found',
                title='Robots not found',
                description='',
                points=100
            )
            return

        if not response.text.strip():
            self.add_violation(
                key='robots.empty',
                title='Empty robots file',
                description='',
                points=100
            )
