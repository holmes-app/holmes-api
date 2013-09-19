#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class JSRequestsValidator(Validator):
    def validate(self):
        js_files = self.get_js_requests()

        self.add_fact(
            key='total.requests.js',
            value=len(js_files)
        )

        results = self.process_js_requests(js_files)

        total_size = sum([len(item.text) for item in results.values()])
        self.add_fact(
            key='total.size.js',
            value=(total_size / 1024.0),
            unit='kb'
        )

        total_size_gzip = sum([len(self.to_gzip(item.text)) for item in results.values()])
        self.add_fact(
            key='total.size.js.gzipped',
            value=(total_size_gzip / 1024.0),
            unit='kb'
        )

    def get_js_requests(self):
        return self.reviewer.html.cssselect('script[src]')

    def process_js_requests(self, js_files):
        results = {}
        for js_file in js_files:
            src = js_file.get('src')
            results[src] = self.get_response(src)

        return results
