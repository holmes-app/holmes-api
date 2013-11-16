#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class TitleFacter(Facter):
    def get_facts(self):
        titles = self.reviewer.current_html.cssselect('title')

        if not titles:
            return

        self.add_fact(
            key='page.title.count',
            value=len(titles),
            title='Page Title Count'
        )

        self.add_fact(
            key='page.title',
            value=titles[0].text,
            title='Page Title'
        )
