#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class RequiredMetaTagsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.meta.tags': {
                'title': _('Required Meta Tags were not found'),
                'description': _("Meta tags for %s were not found."),
                'value_parser': lambda value: ', '.join(value),
                'category': _('HTTP'),
                'generic_description': _(
                    'Validates the absent of user defined MetaTags. '
                    'This values are configurable by Holmes Configuration.'
                ),
                'unit': 'list'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'absent.meta.tags': {
                'value': config.REQUIRED_META_TAGS,
                'description': config.get_description('REQUIRED_META_TAGS')
            }
        }

    def validate(self):
        required_tags = self.get_violation_pref('absent.meta.tags')

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
