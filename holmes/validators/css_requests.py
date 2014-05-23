#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class CSSRequestsValidator(Validator):
    @classmethod
    def get_violation_definitions(cls):
        return {
            'total.requests.css': {
                'title': _('Too many CSS requests'),
                'description': _(
                    'This page has %(total_css_files)d CSS request '
                    '(%(over_limit)d over limit). Having too many '
                    'requests impose a tax in the browser due to handshakes.'),
                'category': _('Performance'),
                'generic_description': _(
                    'Pages with too many CSS requests aren\'t good to '
                    'performance. Overflowing this limit of requests can '
                    'impose a tax in the browser due to handshakes. This '
                    'limit of requests per page is configurable.'
                ),
                'unit': 'number'
            },
            'total.size.css': {
                'title': _('CSS size in kb is too big'),
                'description': _(
                    'There\'s %.2fkb of CSS in this page and that '
                    'adds up to more download time slowing down the '
                    'page rendering to the user.'),
                'category': _('Performance'),
                'generic_description': _(
                    'Pages with too big CSS files aren\'t good to performance. '
                    'Having this limit of file sizes overflow adds up to more '
                    'download time slowing down the page rendering to the user. '
                    'This limit of requests per page is configurable.'
                ),
                'unit': 'number'
            },
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'total.requests.css': {
                'value': config.MAX_CSS_REQUESTS_PER_PAGE,
                'description': config.get_description('MAX_CSS_REQUESTS_PER_PAGE')
            },
            'total.size.css': {
                'value': config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP,
                'description': config.get_description('MAX_CSS_KB_PER_PAGE_AFTER_GZIP')
            }
        }

    def validate(self):
        max_requests_css = self.get_violation_pref('total.requests.css')

        max_size_css_gzipped = self.get_violation_pref('total.size.css')

        total_css_files = self.get_total_requests_css()
        total_size_gzip = self.get_total_size_css_gzipped()

        over_limit = total_css_files - max_requests_css

        if total_css_files > max_requests_css:
            self.add_violation(
                key='total.requests.css',
                value={
                    'total_css_files': total_css_files,
                    'over_limit': over_limit
                },
                points=5 * over_limit
            )

        if total_size_gzip > max_size_css_gzipped:
            self.add_violation(
                key='total.size.css',
                value=total_size_gzip,
                points=int(total_size_gzip - max_size_css_gzipped)
            )

    def get_css_requests(self):
        return self.review.data.get('page.css', None)

    def get_total_requests_css(self):
        return self.review.data.get('total.requests.css', 0)

    def get_total_size_css_gzipped(self):
        return self.review.data.get('total.size.css.gzipped', 0)
