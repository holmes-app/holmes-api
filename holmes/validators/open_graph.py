#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class OpenGraphValidator(Validator):

    @classmethod
    def get_open_graph_message(cls, value):
        return 'Some tags are missing: %s' % (', '.join(value))

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.metatags.open_graph': {
                'title': 'Open Graph tags not found',
                'description': cls.get_open_graph_message
            },
        }

    def validate(self):
        meta_tags = self.get_meta_tags()

        if not meta_tags:
            return

        og = ['og:title', 'og:type', 'og:image', 'og:url']

        for item in meta_tags:
            if item['key'] == 'og:title' and item['content']:
                og.remove('og:title')

            if item['key'] == 'og:type' and item['content']:
                og.remove('og:type')

            if item['key'] == 'og:image' and item['content']:
                og.remove('og:image')

            if item['key'] == 'og:url' and item['content']:
                og.remove('og:url')

        if og:
            self.add_violation(
                key='absent.metatags.open_graph',
                value=og,
                points=50 * len(og)
            )

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
