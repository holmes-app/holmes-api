#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class RequiredMetaTagsValidator(Validator):

    def validate(self):

        required_tags = self.reviewer.config.REQUIRED_META_TAGS
        for tag in required_tags:
            if not self.get_meta_tag(tag):
                self.add_violation(
                    key='absent.meta.%s' % tag,
                    title='Meta not present',
                    description='Not having meta tag for "%s" is '
                                'damaging for Search Engines.' % tag,
                    points=20
                )

    def get_meta_tag(self, tag):
        meta_tags = self.review.data.get('meta.tags', None)
        return [i for i in meta_tags if i['key'] == tag]
