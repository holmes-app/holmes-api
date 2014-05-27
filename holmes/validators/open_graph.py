#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class OpenGraphValidator(Validator):

    @classmethod
    def get_open_graph_parsed_value(cls, value):
        return {'tags': ', '.join(value)}

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.metatags.open_graph': {
                'title': _('Open Graph tags not found'),
                'description': _('Some tags are missing: %(tags)s'),
                'value_parser': cls.get_open_graph_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the absent of Open Graph metatags. '
                    'They allow the Facebook Crawler to generate '
                    'previews when your content is shared on Facebook.'
                )
            },
        }

    def validate(self):
        meta_tags = self.get_meta_tags()

        if not meta_tags:
            return

        og = ['og:title', 'og:type', 'og:image', 'og:url']

        for item in meta_tags:
            og = self._missing_tags(item, 'og:title', og)
            og = self._missing_tags(item, 'og:type', og)
            og = self._missing_tags(item, 'og:image', og)
            og = self._missing_tags(item, 'og:url', og)

        if og:
            self.add_violation(
                key='absent.metatags.open_graph',
                value=og,
                points=50 * len(og)
            )

    def _missing_tags(self, item, key, current_tags):
        if not 'key' in item or not 'content' in item:
            return current_tags

        if item['key'] == key and item['content']:
            if key in current_tags:
                current_tags.remove(key)

        return current_tags

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
