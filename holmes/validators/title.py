#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class TitleValidator(Validator):
    def required_facters(self):
        return ("holmes.facters.title.Title", )

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.title.not_found': {
                'title': 'Page title not found.',
                'description': lambda value: "Title was not found on '%s'." % value
            },
            'page.title.multiple': {
                'title': 'Too many titles.',
                'description': lambda value: "Page '%s' has %d title tags." % (value['page_url'], value['title_count'])
            },
            'page.title.size': {
                'title': 'Maximum size of a page title',
                'description': lambda value: 'Title is too long on "%s". The max size is %d characters.' % (value['page_url'], value['max_size'])
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
        elif len(title) > self.reviewer.config.MAX_TITLE_SIZE:
            self.add_violation(
                key='page.title.size',
                value={
                    'page_url': self.reviewer.page_url,
                    'max_size': self.reviewer.config.MAX_TITLE_SIZE
                },
                points=10
            )
