#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class SchemaOrgItemTypeValidator(Validator):
    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.schema.itemscope': {
                'title': _('itemscope attribute missing in body'),
                'description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemscope attribute.'),
                'category': _('SEO'),
                # TODO: make a better generic_description, more descritive
                'generic_description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemscope attribute.')
            },
            'absent.schema.itemtype': {
                'title': _('itemtype attribute missing in body'),
                'description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemtype attribute.'),
                'category': _('SEO'),
                # TODO: make a better generic_description, more descritive
                'generic_description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemtype attribute.')
            },
            'invalid.schema.itemtype': {
                'title': _('itemtype attribute is invalid'),
                'description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemtype attribute with a value of '
                    '"http://schema.org/WebPage" or '
                    'one of its more specific types.'),
                'category': _('SEO'),
                # TODO: make a better generic_description, more descritive
                'generic_description': _(
                    'In order to conform to schema.org definition '
                    'of a webpage, the body tag must feature an '
                    'itemtype attribute with a value of '
                    '"http://schema.org/WebPage" or '
                    'one of its more specific types.'),
                'unit': 'list'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'invalid.schema.itemtype': {
                'value': config.SCHEMA_ORG_ITEMTYPE,
                'description': config.get_description('SCHEMA_ORG_ITEMTYPE')
            }
        }

    def validate(self):
        itemtype_value = self.get_violation_pref('invalid.schema.itemtype')

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

            if has_itemtype and body.get('itemtype') not in itemtype_value:
                self.add_violation(
                    key='invalid.schema.itemtype',
                    value=None,
                    points=10
                )

    def get_body(self):
        return self.review.data.get('page.body', None)
