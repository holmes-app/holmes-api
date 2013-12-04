#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class BodyFacter(Facter):
    @classmethod
    def get_fact_definitions(cls):
        return {}

    def get_facts(self):

        body = self.reviewer.current_html.cssselect('body')

        if not body:
            return

        self.review.data['page.body'] = body
