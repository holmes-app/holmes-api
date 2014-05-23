#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class JSRequestsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'total.requests.js': {
                'title': _('Too many JavaScript requests'),
                'description': _(
                    'This page has %(total_js_files)d JavaScript request '
                    '(%(over_limit)d over limit). Having too many requests '
                    'impose a tax in the browser due to handshakes.'),
                'category': _('Performance'),
                'generic_description': _(
                    'A site with too many JavaScript requests per page can '
                    'deacrease the page load speed and performance. This '
                    'limits are configurable in Holmes configuration.'
                ),
                'unit': 'number'
            },
            'total.size.js': {
                'title': _('JavaScript size in kb is too big'),
                'description': _(
                    'There\'s %.2fkb of JavaScript in this page and '
                    'that adds up to more download time slowing down '
                    'the page rendering to the user.'),
                'category': _('Performance'),
                'generic_description': _(
                    'A site with a too big total JavaScript size per page can '
                    'decrease the page load speed and performance. This '
                    'limits are configurable in Holmes configuration.'
                ),
                'unit': 'number'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'total.size.js': {
                'value': config.MAX_JS_KB_PER_PAGE_AFTER_GZIP,
                'description': config.get_description('MAX_JS_KB_PER_PAGE_AFTER_GZIP')
            },
            'total.requests.js': {
                'value': config.MAX_JS_REQUESTS_PER_PAGE,
                'description': config.get_description('MAX_JS_REQUESTS_PER_PAGE')
            }
        }

    def validate(self):
        max_size_js = self.get_violation_pref('total.size.js')

        max_requests_js = self.get_violation_pref('total.requests.js')

        total_js_files = self.get_total_requests_js()
        total_size_gzip = self.get_total_size_js_gzipped()

        over_limit = total_js_files - max_requests_js

        if total_js_files > max_requests_js:
            self.add_violation(
                key='total.requests.js',
                value={
                    'total_js_files': total_js_files,
                    'over_limit': over_limit},
                points=5 * over_limit
            )

        if total_size_gzip > max_size_js:
            self.add_violation(
                key='total.size.js',
                value=total_size_gzip,
                points=int(total_size_gzip - max_size_js)
            )

    def get_js_requests(self):
        return self.review.data.get('page.js', None)

    def get_total_requests_js(self):
        return self.review.data.get('total.requests.js', 0)

    def get_total_size_js(self):
        return self.review.data.get('total.size.js', 0)

    def get_total_size_js_gzipped(self):
        return self.review.data.get('total.size.js.gzipped', 0)
