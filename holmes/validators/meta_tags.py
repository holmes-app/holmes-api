#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class MetaTagsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.metatags': {
                'title': 'Meta tags not present',
                'description': lambda value: (
                    "No meta tags found on this page. This is damaging for "
                    "Search Engines."
                ),
                'category': 'HTTP'
            },
            'page.metatags.description_too_big': {
                'title': 'Maximum size of description meta tag',
                'description': lambda value: (
                    "The meta description tag is longer than %s characters. "
                    "It is best to keep meta descriptions shorter for better "
                    "indexing on Search engines."
                ) % value['max_size'],
                'category': 'SEO'
            }
        }

    def validate(self):
        meta_tags = self.review.data.get('meta.tags', None)

        if not meta_tags:
            self.add_violation(
                key='absent.metatags',
                value='No metatags.',
                points=100
            )

        max_size = self.config.METATAG_DESCRIPTION_MAX_SIZE
        for mt in meta_tags:
            if mt['key'] == 'description' and len(mt['content']) > max_size:
                self.add_violation(
                    key='page.metatags.description_too_big',
                    value={'max_size': max_size},
                    points=20
                )
                break
