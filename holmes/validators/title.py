#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class TitleValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.title.not_found': {
                'title': 'Page title not found',
                'description': lambda value: "Title was not found on '%s'." % value,
                'category': 'HTTP',
                'generic_description': (
                    'Validates the presence of the page\'s title. '
                    'The <title> tag is required in all HTML documents '
                    'and it defines the title of the document.'
                )
            },
            'page.title.multiple': {
                'title': 'Too many titles',
                'description': lambda value: "Page '%s' has %d title tags." % (value['page_url'], value['title_count']),
                'category': 'Semantics',
                'generic_description': (
                    'Validates the presence of more than one page\'s title tag.'
                )
            },
            'page.title.size': {
                'title': 'Maximum size of a page title',
                'description': lambda value: 'Title is too long on "%s". The max size is %d characters.' % (value['page_url'], value['max_size']),
                'category': 'SEO',
                'generic_description': 'Validates the size of the page\'s title.'
            }
        }

    def validate(self):
        title_count = self.review.data.get('page.title_count', 0)
        title = self.review.facts.get('page.title', None)

        if not title_count or not title:
            self.add_violation(
                key='page.title.not_found',
                value=self.reviewer.page_url,
                points=50
            )
            return

        if title_count > 1:
            self.add_violation(
                key='page.title.multiple',
                value={
                    'page_url': self.reviewer.page_url,
                    'title_count': title_count
                },
                points=50
            )
        elif len(title) > self.config.MAX_TITLE_SIZE:
            self.add_violation(
                key='page.title.size',
                value={
                    'page_url': self.reviewer.page_url,
                    'max_size': self.config.MAX_TITLE_SIZE
                },
                points=10
            )
