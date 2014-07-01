#!/usr/bin/python
# -*- coding: utf-8 -*-

# Deferred imports
try:
    from urllib.parse import urlparse  # Py3
except ImportError:
    from urlparse import urlparse

from holmes.utils import is_valid, _
from holmes.validators.base import Validator


class LinkWithRelCanonicalValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.meta.canonical': {
                'title': _('Link with rel="canonical" not found'),
                'description': _(
                    'As can be seen in this page '
                    '<a href="https://support.google.com/webmasters/answer/'
                    '139394?hl=en">About rel="canonical"</a>, it\'s a good '
                    'practice to include rel="canonical" urls in the pages '
                    'for your website.'
                ),
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the absent of link with rel="canonical" on '
                    'the head of a page. This indicates the preferred URL '
                    'to use to access the green dress post, so that the '
                    'search results will be more likely to show users '
                    'that URL structure.'
                ),
                'unit': 'boolean'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'absent.meta.canonical': {
                'value': config.FORCE_CANONICAL,
                'description': config.get_description('FORCE_CANONICAL')
            }
        }

    def validate(self):
        force_canonical = self.get_violation_pref('absent.meta.canonical')

        if not force_canonical:
            # Only pages with query string parameters
            if self.page_url:
                if not is_valid(self.page_url):
                    return

                if not urlparse(self.page_url).query:
                    return

        head = self.get_head()
        if head:
            canonical = [item for item in head if item.get('rel') == 'canonical']

            if not canonical:
                self.add_violation(
                    key='absent.meta.canonical',
                    value=None,
                    points=30
                )

    def get_head(self):
        return self.review.data.get('page.head', None)
