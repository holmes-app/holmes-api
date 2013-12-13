#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class RobotsValidator(Validator):

    SITEMAP_NOT_FOUND = 'You must specify the location of the Sitemap ' \
                        'using a robots.txt file'

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
            },
            'robots.sitemap.not_found': {
                'title': 'Sitemap in Robots not found',
                'description': lambda value: cls.SITEMAP_NOT_FOUND
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
            return

        has_sitemap = False
        for rawline in response.text.splitlines():
            line = rawline.strip()
            comments = line.find('#')
            if comments >= 0:
                line = line[:comments]
            if line == '' or ':' not in line:
                continue
            key, val = [x.strip() for x in line.split(':', 1)]
            key = key.lower()
            if key == 'sitemap':
                has_sitemap = True

        if not has_sitemap:
            self.add_violation(
                key='robots.sitemap.not_found',
                value=None,
                points=100
            )
