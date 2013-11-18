#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class JSFacter(Facter):

    def get_facts(self):
        js_files = self.get_js_requests()

        self.review.data['page.js'] = set()
        self.review.data['total.size.js'] = 0
        self.review.data['total.size.js.gzipped'] = 0

        self.add_fact(
            key='page.js',
            value=set(),
            title='JS',
            unit='js'
        )

        self.add_fact(
            key='total.size.js',
            value=0,
            unit='kb',
            title='Total JS size'
        )

        self.add_fact(
            key='total.size.js.gzipped',
            value=0,
            unit='kb',
            title='Total JS size gzipped'
        )

        num_js = 0

        js_to_get = set()

        for js_file in js_files:
            src = js_file.get('src')

            if not self.is_absolute(src):
                src = self.rebase(src)

            js_to_get.add(src)
            num_js += 1

        self.add_fact(
            key='total.requests.js',
            value=num_js,
            title='Total JS requests'
        )

        for url in js_to_get:
            self.async_get(url, self.handle_url_loaded)

    def handle_url_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))

        self.review.facts['page.js']['value'].add(url)
        self.review.data['page.js'].add((url, response))

        size_js = len(response.content) / 1024.0
        self.review.facts['total.size.js']['value'] += size_js
        self.review.data['total.size.js'] += size_js

        size_gzip = len(self.to_gzip(response.content)) / 1024.0
        self.review.facts['total.size.js.gzipped']['value'] += size_gzip
        self.review.data['total.size.js.gzipped'] += size_gzip

    def get_js_requests(self):
        return self.reviewer.current_html.cssselect('script[src]')
