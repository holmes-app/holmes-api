#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class TotalRequestsValidator(Validator):
    def validate(self):
        css_files = self.get_css_requests()
        js_files = self.get_js_requests()
        img_files = self.get_img_requests()

        self.add_fact(
            key='total.requests',
            value=len(css_files) + len(js_files) + len(img_files),
            title='Total requests'
        )

    def get_css_requests(self):
        return self.reviewer.current_html.cssselect('link[href]')

    def get_js_requests(self):
        return self.reviewer.current_html.cssselect('script[src]')

    def get_img_requests(self):
        return self.reviewer.current_html.cssselect('img[src]')
