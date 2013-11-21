#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class SchemaOrgItemTypeValidator(Validator):

    def validate(self):
        body = self.get_body()

        if len(body) <= 1:

            if body:
                body = body[0]
                attributes = body.keys()
            else:
                attributes = []

            if 'itemscope' not in attributes:
                self.add_violation(
                    key='absent.schema.itemscope',
                    title='itemscope attribute missing in body',
                    description='In order to conform to schema.org definition '
                                'of a webpage, the body tag must feature an '
                                'itemscope attribute.',
                    points=10)

            has_itemtype = 'itemtype' in attributes
            if not has_itemtype:
                self.add_violation(
                    key='absent.schema.itemtype',
                    title='itemtype attribute missing in body',
                    description='In order to conform to schema.org definition '
                                'of a webpage, the body tag must feature an '
                                'itemtype attribute.',
                    points=10
                )

            itemtype_value = ['http://schema.org/WebPage',
                              'http://schema.org/AboutPage',
                              'http://schema.org/CheckoutPage',
                              'http://schema.org/CollectionPage',
                              'http://schema.org/ContactPage',
                              'http://schema.org/ItemPage',
                              'http://schema.org/MedicalWebPage',
                              'http://schema.org/ProfilePage',
                              'http://schema.org/SearchResultsPage']

            if not has_itemtype or body.get('itemtype') not in itemtype_value:
                url = itemtype_value[0]
                self.add_violation(
                    key='invalid.schema.itemtype',
                    title='itemtype attribute is invalid',
                    description='In order to conform to schema.org definition '
                                'of a webpage, the body tag must feature an '
                                'itemtype attribute with a value of "%s" or '
                                'one of its more specific types.' % (url),
                    points=10
                )

    def get_body(self):
        return self.review.data.get('page.body', None)
