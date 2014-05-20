#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class RequiredMetaTagsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.meta.tags': {
                'title': 'Required Meta Tags were not found',
                'description': lambda value: "Meta tags for %s were not found." % (', '.join(value)),
                'category': 'HTTP',
                'generic_description': (
                    'Validates the absent of user defined MetaTags. '
                    'This values are configurable by Holmes Configuration.'
                )
            }
        }

    def validate(self):
        required_tags = self.reviewer.config.REQUIRED_META_TAGS

        absent_metatags = []

        for tag in required_tags:
            if not self.get_meta_tag(tag):
                absent_metatags.append(tag)

        if absent_metatags:
            self.add_violation(
                key='absent.meta.tags',
                value=absent_metatags,
                points=20
            )

    def get_meta_tag(self, tag):
        meta_tags = self.review.data.get('meta.tags', None)
        return [i for i in meta_tags if i['key'] == tag]
