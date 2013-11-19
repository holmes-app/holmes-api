#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class LinkWithRedirectValidator(Validator):

    def validate(self):
        links = self.get_links()

        for url, response in links:
            if response.status_code in [302, 307]:
                self.add_violation(
                    key='link.redirect.%d' % response.status_code,
                    title='Link with %d redirect' % response.status_code,
                    description='Link with redirect, in most cases, should '
                                'not be used. Redirects were found for '
                                'link: %s.' % url,
                    points=10
                )

    def get_links(self):
        return self.review.data.get('page.links', None)
