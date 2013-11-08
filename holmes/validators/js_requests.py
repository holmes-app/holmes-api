#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class JSRequestsValidator(Validator):
    def validate(self):
        js_files = self.get_js_requests()

        self.add_fact(
            key='total.requests.js',
            value=len(js_files),
            title='Total JS requests'
        )

        results = self.process_js_requests(js_files)

        total_size = sum([len(item['content']) for item in results.values()]) / 1024.0
        self.add_fact(
            key='total.size.js',
            value=total_size,
            unit='kb',
            title='Total JS size'
        )

        total_size_gzip = sum([len(self.to_gzip(item['content'])) for item in results.values()]) / 1024.0
        self.add_fact(
            key='total.size.js.gzipped',
            value=total_size_gzip,
            unit='kb',
            title='Total JS size gzipped'
        )

        if len(js_files) > self.reviewer.config.MAX_JS_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.js',
                title='Too many javascript requests.',
                description='This page has %d javascript request (%d over limit). Having too many requests impose a tax in the browser due to handshakes.' % (
                    len(js_files), len(js_files) - self.reviewer.config.MAX_JS_REQUESTS_PER_PAGE
                ),
                points=5 * (len(js_files) - self.reviewer.config.MAX_JS_REQUESTS_PER_PAGE)
            )

        if total_size_gzip > self.reviewer.config.MAX_JS_KB_PER_PAGE_AFTER_GZIP:
            self.add_violation(
                key='total.size.js',
                title='Javascript size in kb is too big.',
                description="There's %.2fkb of Javascript in this page and that adds up to more download time slowing down the page rendering to the user." % total_size_gzip,
                points=int(total_size_gzip - self.reviewer.config.MAX_JS_KB_PER_PAGE_AFTER_GZIP)
            )

    def get_js_requests(self):
        return self.reviewer.current_html.cssselect('script[src]')

    def process_js_requests(self, js_files):
        results = {}
        for js_file in js_files:
            src = js_file.get('src')
            results[src] = self.get_response(src)

        return results
