#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class HeadingHierarchyValidator(Validator):

    @classmethod
    def get_violation_description(cls, value):
        return (
            'Heading hierarchy values bigger than %s characters aren\'t good '
            'for Search Engines. This elements were found:'
            '<ul class="violation-hh-list">%s</ul>' % (
                value['max_size'],
                ''.join([
                    '<li><span class="hh-type">%s</span>: %s</li>' % (key, desc)
                    for key, desc in value['hh_list']
                ])
            )
        )

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.heading_hierarchy.size': {
                'title': 'Maximum size of a heading hierarchy',
                'description': cls.get_violation_description,
                'category': 'SEO',
                'generic_description': (
                    'Heading hierarchy tags with values too big aren\'t good '
                    'for search engines. The definition of this maximum size '
                    'can be configurable on Holmes.'
                )
            }
        }

    def validate(self):
        hh_list = self.review.data.get('page.heading_hierarchy', [])

        violations = []
        for key, desc in hh_list:
            if len(desc) > self.config.MAX_HEADING_HIEARARCHY_SIZE:
                violations.append((key, desc))

        if violations:
            self.add_violation(
                key='page.heading_hierarchy.size',
                value={
                    'max_size': self.config.MAX_HEADING_HIEARARCHY_SIZE,
                    'hh_list': violations
                },
                points=20 * len(violations)
            )


class H1HeadingValidator(Validator):

    @classmethod
    def get_violation_description(cls, value=None):
        return (
            'Your page does not contain any H1 headings. H1 headings help '
            'indicate the important topics of your page to search engines. '
            'While less important than good meta-titles and descriptions, '
            'H1 headings may still help define the topic of your page to '
            'search engines.'
        )

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.heading_hierarchy.h1_not_found': {
                'title': 'H1 Headings not found',
                'description': cls.get_violation_description,
                'category': 'SEO',
                'generic_description': (
                    'H1 headings help indicate the important topics of your '
                    'page to search engines. While less important than good '
                    'meta-titles and descriptions, H1 headings may still '
                    'help define the topic of your page to search engines.'
                )
            }
        }

    def validate(self):
        hh_list = self.review.data.get('page.heading_hierarchy', [])
        for key, desc in hh_list:
            if key == 'h1':
                return

        self.add_violation(
            key='page.heading_hierarchy.h1_not_found',
            value=None,
            points=30
        )
