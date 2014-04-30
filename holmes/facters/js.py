#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class JSFacter(Facter):
    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.js': {
                'title': 'JS',
                'description': lambda value: list(value),
                'unit': 'js',
                'category': 'Static',
            },
            'total.requests.js': {
                'title': 'Total JS requests',
                'description': lambda value: value,
                'category': 'HTTP',
                'unit': 'number'
            },
            'total.size.js': {
                'title': 'Total JS size',
                'description': lambda value: '%d' % value,
                'unit': 'kb',
                'category': 'SEO',
            },
            'total.size.js.gzipped': {
                'title': 'Total JS size gzipped',
                'description': lambda value: '%d' % value,
                'unit': 'kb',
                'category': 'SEO'
            }
        }

    def get_facts(self):
        js_files = self.get_js_requests()

        self.review.data['page.js'] = set()
        self.review.data['total.size.js'] = 0
        self.review.data['total.size.js.gzipped'] = 0

        self.add_fact(
            key='page.js',
            value=set(),
        )

        self.add_fact(
            key='total.size.js',
            value=0,
        )

        self.add_fact(
            key='total.size.js.gzipped',
            value=0,
        )

        num_js = 0

        js_to_get = set()

        for js_file in js_files:
            src = js_file.get('src')

            src = self.normalize_url(src)
            if src:
                js_to_get.add(src)
                num_js += 1

        self.add_fact(
            key='total.requests.js',
            value=num_js,
        )

        for url in js_to_get:
            self.async_get(url, self.handle_url_loaded)

    def handle_url_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))

        self.review.facts['page.js']['value'].add(url)
        self.review.data['page.js'].add((url, response))

        if response.text:
            size_js = len(response.text) / 1024.0
            size_gzip = len(self.to_gzip(response.text)) / 1024.0
        else:
            size_js = 0
            size_gzip = 0

        self.review.facts['total.size.js']['value'] += size_js
        self.review.data['total.size.js'] += size_js

        self.review.facts['total.size.js.gzipped']['value'] += size_gzip
        self.review.data['total.size.js.gzipped'] += size_gzip

    def get_js_requests(self):
        return self.reviewer.current_html.cssselect('script[src]')
