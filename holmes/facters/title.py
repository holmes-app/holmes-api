#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class TitleFacter(Facter):
    def get_facts(self):
        titles = self.reviewer.current_html.cssselect('title')

        if not titles:
            return

        self.review.data['page.title.count'] = len(titles)

        self.add_fact(
            key='page.title',
            value=titles[0].text,
            title='Page Title'
        )
