#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import dumps

from holmes.validators.base import Validator


class MetaTagsValidator(Validator):

    def validate(self):
        values = dumps(self.process_meta_tags())

        self.add_fact(
            key='meta.tags',
            value=values,
            title='Meta Tags',
            unit='values'
        )

    def get_meta_tags(self):
        meta_tags = self.reviewer.current_html.cssselect('meta')
        values = []
        for tags in meta_tags:
           values.append(dict(tags.items()))
        return values

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


        Case 3: {'content': 'text\\/html;charset=UTF-8', 'http-equiv': 'Content-Type'}

        KEY => 'Content-Type'
        CONTENT => 'text\\/html;charset=UTF-8'
        PROPERTY => 'http-equiv'
        """

        arrAux = []
        for x in self.get_meta_tags():
            if len(x) == 1:
                key = x.iterkeys().next()
                content = x.itervalues().next()
                prop = None
            elif len(x) > 1:
                if 'content' in x:
                    content = x.get('content')
                    x.pop('content')
                else:
                    content = None
                key = x.itervalues().next()
                prop = x.iterkeys().next()
            arrAux.append({'key': key, 'content': content, 'property': prop})
        return arrAux
