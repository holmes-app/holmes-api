#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class CSSRequestsValidator(Validator):
    @classmethod
    def get_requests_css_message(cls, value):
        return 'This page has %d CSS request (%d over limit). ' \
               'Having too many requests impose a tax in the ' \
               'browser due to handshakes.' % (value['total_css_files'],
                                               value['over_limit'])

    @classmethod
    def get_total_size_message(cls, value):
        return 'There\'s %.2fkb of CSS in this page and that ' \
               'adds up to more download time slowing down the ' \
               'page rendering to the user.' % value

    @classmethod
    def get_violation_definitions(cls):
        return {
            'total.requests.css': {
                'title': 'Too many CSS requests',
                'description': cls.get_requests_css_message,
                'category': 'Performance',
                'generic_description': (
                    'Pages with too many CSS requests aren\'t good to '
                    'performance. Overflowing this limit of requests can '
                    'impose a tax in the browser due to handshakes. This '
                    'limit of requests per page is configurable.'
                ),
            },
            'total.size.css': {
                'title': 'CSS size in kb is too big',
                'description': cls.get_total_size_message,
                'category': 'Performance',
                'generic_description': (
                    'Pages with too big CSS files aren\'t good to performance. '
                    'Having this limit of file sizes overflow adds up to more '
                    'download time slowing down the page rendering to the user. '
                    'This limit of requests per page is configurable.'
                ),
            },
        }

    def validate(self):
        total_css_files = self.get_total_requests_css()
        total_size_gzip = self.get_total_size_css_gzipped()

        max_requests = self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE
        over_limit = total_css_files - max_requests

        if total_css_files > self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.css',
                value={
                    'total_css_files': total_css_files,
                    'over_limit': over_limit
                },
                points=5 * over_limit
            )

        max_kb_gzip = self.reviewer.config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP

        if total_size_gzip > max_kb_gzip:
            self.add_violation(
                key='total.size.css',
                value=total_size_gzip,
                points=int(total_size_gzip - max_kb_gzip)
            )

    def get_css_requests(self):
        return self.review.data.get('page.css', None)

    def get_total_requests_css(self):
        return self.review.data.get('total.requests.css', 0)

    def get_total_size_css_gzipped(self):
        return self.review.data.get('total.size.css.gzipped', 0)
