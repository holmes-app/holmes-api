#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class MetaTagsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.metatags': {
                'title': 'Meta tags not present.',
                'description': lambda value: "No meta tags found on this page. This is damaging for Search Engines."
            }
        }

    def validate(self):
        meta_tags = self.get_meta_tags()

        if not meta_tags:
            self.add_violation(
                key='absent.metatags',
                value='No metatags.',
                points=100
            )

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
