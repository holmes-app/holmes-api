#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class TitleValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.title.not_found': {
                'title': _('Page title not found'),
                'description': _("Title was not found on '%s'."),
                'category': _('HTTP'),
                'generic_description': _(
                    'Validates the presence of the page\'s title. '
                    'The <title> tag is required in all HTML documents '
                    'and it defines the title of the document.'
                )
            },
            'page.title.multiple': {
                'title': _('Too many titles'),
                'description': _(
                    "Page '%(page_url)s' has %(title_count)d title tags."),
                'category': _('Semantics'),
                'generic_description': _(
                    'Validates the presence of more than one page\'s title '
                    'tag.'
                )
            },
            'page.title.size': {
                'title': _('Maximum size of a page title'),
                'description': _(
                    'Title is too long on "%(page_url)s". '
                    'The max size is %(max_size)d characters.'),
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the size of the page\'s title.'),
                'unit': 'number'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'page.title.size': {
                'value': config.MAX_TITLE_SIZE,
                'description': config.get_description('MAX_TITLE_SIZE')
            }
        }

    def validate(self):
        max_title_size = self.get_violation_pref('page.title.size')

        title_count = self.review.data.get('page.title_count', 0)
        title = self.review.data.get('page.title', None)

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
        elif max_title_size and len(title) > int(max_title_size):
            self.add_violation(
                key='page.title.size',
                value={
                    'page_url': self.reviewer.page_url,
                    'max_size': int(max_title_size)
                },
                points=10
            )
