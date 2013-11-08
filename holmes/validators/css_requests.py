#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class CSSRequestsValidator(Validator):
    def validate(self):
        css_files = self.get_css_requests()

        self.add_fact(
            key='total.requests.css',
            value=len(css_files),
            title='Total CSS requests'
        )

        results = self.process_css_requests(css_files)

        total_size = sum([len(item['content']) for item in results.values()]) / 1024.0
        self.add_fact(
            key='total.size.css',
            value=total_size,
            unit='kb',
            title='Total CSS size'
        )

        total_size_gzip = sum([len(self.to_gzip(item['content'])) for item in results.values()]) / 1024.0
        self.add_fact(
            key='total.size.css.gzipped',
            value=total_size_gzip,
            unit='kb',
            title='Total CSS size gzipped'
        )

        if len(css_files) > self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.css',
                title='Too many CSS requests.',
                description='This page has %d CSS request (%d over limit). Having too many requests impose a tax in the browser due to handshakes.' % (
                    len(css_files), len(css_files) - self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE
                ),
                points=5 * (len(css_files) - self.reviewer.config.MAX_CSS_REQUESTS_PER_PAGE)
            )

        if total_size_gzip > self.reviewer.config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP:
            self.add_violation(
                key='total.size.css',
                title='CSS size in kb is too big.',
                description="There's %.2fkb of CSS in this page and that adds up to more download time slowing down the page rendering to the user." % total_size_gzip,
                points=int(total_size_gzip - self.reviewer.config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP)
            )

    def get_css_requests(self):
        return self.reviewer.current_html.cssselect('link[href]')

    def process_css_requests(self, css_files):
        results = {}
        for css_file in css_files:
            src = css_file.get('href')
            if not src.endswith('.css'):
                continue
            results[src] = self.get_response(src)

        return results
