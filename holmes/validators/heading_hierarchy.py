#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class HeadingHierarchyValidator(Validator):

    @classmethod
    def get_violation_parsed_value(cls, value):
        return {
            'max_size': value['max_size'],
            'hh_list': ''.join([
                '<li><span class="hh-type">%s</span>: %s</li>' % (key, desc)
                for key, desc in value['hh_list']
            ])
        }

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.heading_hierarchy.size': {
                'title': _('Maximum size of a heading hierarchy'),
                'description': _(
                    'Heading hierarchy values bigger than %(max_size)s '
                    'characters aren\'t good for Search Engines. This '
                    'elements were found: '
                    '<ul class="violation-hh-list">%(hh_list)s</ul>'),
                'value_parser': cls.get_violation_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Heading hierarchy tags with values too big aren\'t good '
                    'for search engines. The definition of this maximum size '
                    'can be configurable on Holmes.'
                ),
                'unit': 'number'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'page.heading_hierarchy.size': {
                'value': config.MAX_HEADING_HIEARARCHY_SIZE,
                'description': config.get_description('MAX_HEADING_HIEARARCHY_SIZE')
            }
        }

    def validate(self):
        max_heading_size = self.get_violation_pref('page.heading_hierarchy.size')

        hh_list = self.review.data.get('page.heading_hierarchy', [])

        violations = []
        for key, desc in hh_list:
            if len(desc) > max_heading_size:
                violations.append((key, desc))

        if violations:
            self.add_violation(
                key='page.heading_hierarchy.size',
                value={
                    'max_size': max_heading_size,
                    'hh_list': violations
                },
                points=20 * len(violations)
            )


class H1HeadingValidator(Validator):
    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.heading_hierarchy.h1_not_found': {
                'title': _('H1 Headings not found'),
                'description': _(
                    'Your page does not contain any H1 headings. H1 headings '
                    'help indicate the important topics of your page to '
                    'search engines. While less important than good '
                    'meta-titles and descriptions, H1 headings may still '
                    'help define the topic of your page to search engines.'
                ),
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
