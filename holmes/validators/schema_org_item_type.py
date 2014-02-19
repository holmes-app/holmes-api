#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class SchemaOrgItemTypeValidator(Validator):
    @classmethod
    def get_itemscope_message(cls, value=None):
        return 'In order to conform to schema.org definition ' \
               'of a webpage, the body tag must feature an ' \
               'itemscope attribute.'

    @classmethod
    def get_itemtype_message(cls, value=None):
        return 'In order to conform to schema.org definition ' \
               'of a webpage, the body tag must feature an ' \
               'itemtype attribute.'

    @classmethod
    def get_invalid_itemtype_message(cls, value=None):
        url = 'http://schema.org/WebPage'
        return 'In order to conform to schema.org definition ' \
               'of a webpage, the body tag must feature an ' \
               'itemtype attribute with a value of "%s" or ' \
               'one of its more specific types.' % url

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.schema.itemscope': {
                'title': 'itemscope attribute missing in body',
                'description': cls.get_itemscope_message,
                'category': 'SEO'
            },
            'absent.schema.itemtype': {
                'title': 'itemtype attribute missing in body',
                'description': cls.get_itemtype_message,
                'category': 'SEO'
            },
            'invalid.schema.itemtype': {
                'title': 'itemtype attribute is invalid',
                'description': cls.get_invalid_itemtype_message,
                'category': 'SEO'
            }
        }

    def validate(self):
        body = self.get_body()

        if not body:
            return

        if len(body) == 1:

            body = body[0]
            attributes = body.keys()

            if 'itemscope' not in attributes:
                self.add_violation(
                    key='absent.schema.itemscope',
                    value=None,
                    points=10)

            has_itemtype = 'itemtype' in attributes
            if not has_itemtype:
                self.add_violation(
                    key='absent.schema.itemtype',
                    value=None,
                    points=10
                )

            itemtype_value = self.reviewer.config.SCHEMA_ORG_ITEMTYPE
            if has_itemtype and body.get('itemtype') not in itemtype_value:
                self.add_violation(
                    key='invalid.schema.itemtype',
                    value=None,
                    points=10
                )

    def get_body(self):
        return self.review.data.get('page.body', None)
