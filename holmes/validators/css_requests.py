#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class CSSRequestsValidator(Validator):

    def validate(self):
        total_css_files = self.get_total_requests_css()
        total_size_gzip = self.get_total_size_css_gzipped()

        max_requests = self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE
        over_limit = total_css_files - max_requests

        if total_css_files > self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.css',
                title='Too many CSS requests.',
                description='This page has %d CSS request (%d over limit). '
                            'Having too many requests impose a tax in the '
                            'browser due to handshakes.' % (total_css_files,
                                                            over_limit),
                points=5 * over_limit
            )

        max_kb_gzip = self.reviewer.config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP

        if total_size_gzip > max_kb_gzip:
            self.add_violation(
                key='total.size.css',
                title='CSS size in kb is too big.',
                description='There\'s %.2fkb of CSS in this page and that '
                            'adds up to more download time slowing down the '
                            'page rendering to the user.' % total_size_gzip,
                points=int(total_size_gzip - max_kb_gzip)
            )

    def get_css_requests(self):
        return self.review.data.get('page.css', None)

    def get_total_requests_css(self):
        return self.review.data.get('total.requests.css', 0)

    def get_total_size_css_gzipped(self):
        return self.review.data.get('total.size.css.gzipped', 0)
