#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class MetaTagsFacter(Facter):

    @classmethod
    def get_fact_definitions(cls):
        return {
            'meta.tags': {
                'title': 'Meta Tags',
                'description': lambda value: value,
                'unit': 'values',
                'category': 'Meta',
            }
        }

    def get_facts(self):

        values = self.process_meta_tags()

        self.add_fact(
            key='meta.tags',
            value=values,
        )

        self.review.data['meta.tags'] = values

    def process_meta_tags(self):
        """
        Case 1: {'charset': 'utf-8'}

        KEY => 'charset'
        CONTENT => 'utf-8'
        PROPERTY =>


        Case 2: {"content":"website","property":"og:type"}

        KEY => 'og:type'
        CONTENT => 'website'
        PROPERTY => 'property'


        Case 3: {'content': 'text\\/html;charset=UTF-8',
                 'http-equiv': 'Content-Type'}

        KEY => 'Content-Type'
        CONTENT => 'text\\/html;charset=UTF-8'
        PROPERTY => 'http-equiv'
        """

        data = []
        for tag in self.get_meta_tags():
            if len(tag) == 1:
                key = tag.iterkeys().next()
                content = tag.itervalues().next()
                prop = None
            elif len(tag) > 1:
                if 'content' in tag:
                    content = tag.get('content')
                    tag.pop('content')
                else:
                    content = None
                key = tag.itervalues().next()
                prop = tag.iterkeys().next()
            data.append({'key': key, 'content': content, 'property': prop})
        return data

    def get_meta_tags(self):
        meta_tags = self.reviewer.current_html.cssselect('meta')
        values = []
        for tags in meta_tags:
            values.append(dict(tags.items()))
        return values
