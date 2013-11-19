#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class MetaTagsValidator(Validator):

    def validate(self):
        meta_tags = self.get_meta_tags()

        if not meta_tags:
            self.add_violation(
                key='absent.metatags',
                title='Meta tags not present',
                description='Not having meta tags is damaging for '
                            'Search Engines.',
                points=100
            )

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
