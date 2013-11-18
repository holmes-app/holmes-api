#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class JSRequestsValidator(Validator):
    def validate(self):
        total_js_files = self.get_total_requests_js()
        total_size_gzip = self.get_total_size_js_gzipped()

        max_requests = self.reviewer.config.MAX_JS_REQUESTS_PER_PAGE
        over_limit = total_js_files - max_requests

        if total_js_files > max_requests:
            self.add_violation(
                key='total.requests.js',
                title='Too many javascript requests.',
                description='This page has %d JavaScript request '
                            '(%d over limit). Having too many requests impose '
                            'a tax in the browser due to handshakes.' % (
                                total_js_files,
                                over_limit),
                points=5 * over_limit
            )

        max_kb_gzip = self.reviewer.config.MAX_JS_KB_PER_PAGE_AFTER_GZIP

        if total_size_gzip > max_kb_gzip:
            self.add_violation(
                key='total.size.js',
                title='Javascript size in kb is too big.',
                description='There\'s %.2fkb of JavaScript in this page and '
                            'that adds up to more download time slowing down '
                            'the page rendering to the user.' % total_size_gzip,
                points=int(total_size_gzip - max_kb_gzip)
            )

    def get_js_requests(self):
        return self.review.data.get('page.js', None)

    def get_total_requests_js(self):
        return self.review.data.get('total.requests.js', 0)

    def get_total_size_js(self):
        return self.review.data.get('total.size.js', 0)

    def get_total_size_js_gzipped(self):
        return self.review.data.get('total.size.js.gzipped', 0)
