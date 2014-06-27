#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter
from holmes.utils import _


class TitleFacter(Facter):

    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.title': {
                'title': _('Page Title'),
                'description': lambda value: value,
                'category': _('SEO'),
            }
        }

    def get_facts(self):
        titles = self.reviewer.current_html.cssselect('title')

        if not titles:
            return

        if not titles[0].text:
            return

        self.review.data['page.title_count'] = len(titles)

        title = titles[0].text.strip()

        self.review.data['page.title'] = title
        self.add_fact(key='page.title', value=title)
