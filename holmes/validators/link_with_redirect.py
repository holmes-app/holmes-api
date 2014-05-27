#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class LinkWithRedirectValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'link.redirect.302': {
                'title': _('Link with 302 redirect'),
                'description': _(
                    'Link with 302 redirect, in most cases, should '
                    'not be used. Redirects were found for '
                    'link: %s.'),
                'category': _('HTTP'),
                'generic_description': _(
                    'Validates temporary redirections (302). '
                    'They should not be used in the most cases, instead '
                    'is best to use a 301 permanent redirect.'
                )
            },
            'link.redirect.307': {
                'title': _('Link with 307 redirect'),
                'description': _(
                    'Link with 307 redirect, in most cases, should '
                    'not be used. Redirects were found for '
                    'link: %s.'),
                'category': _('HTTP'),
                'generic_description': _(
                    'Validates temporary redirections (307). '
                    'They should not be used in the most cases, instead '
                    'is best to use a 301 permanent redirect.'
                )
            },
        }

    def validate(self):
        links = self.get_links()

        for url, response in links:
            if response.status_code in [302, 307]:
                self.add_violation(
                    key='link.redirect.%d' % response.status_code,
                    value=response.status_code,
                    points=10
                )

    def get_links(self):
        return self.review.data.get('page.links', None)
