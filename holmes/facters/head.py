#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class HeadFacter(Facter):
    @classmethod
    def get_fact_definitions(cls):
        return {}

    def get_facts(self):
        head = self.reviewer.current_html.cssselect('head')

        if not head:
            return

        self.review.data['page.head'] = head
