#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator
from holmes.utils import get_domain_from_url


class RobotsValidator(Validator):
    def validate(self):
        result = self.get_robots_from_domain()

        if result.get('status') > 399:
            self.add_violation(
                key='robots.not_found',
                title='Robots not found',
                description='',
                points=100
            )
            return

        if not result.get('content'):
            self.add_violation(
                key='robots.empty',
                title='Empty robots file',
                description='',
                points=100
            )

    def get_robots_from_domain(self):
        return self.get_response("%srobots.txt" % get_domain_from_url(self.page_url)[1])
