#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import is_valid
from holmes.validators.base import Validator


class UrlWithUnderscoreValidator(Validator):

    @classmethod
    def get_url_with_underscore_message(cls, value=None):
        return ('Google treats a hyphen as a word separator, but does '
                'not treat an underscore that way. Google treats and '
                'underscore as a word joiner — so red_sneakers is the '
                'same as redsneakers to Google. This has been confirmed '
                'directly by Google themselves, including the fact that '
                'using dashes over underscores will have a (minor) '
                'ranking benefit.')

    @classmethod
    def get_violation_definitions(cls):
        return {
            'invalid.url_word_separator': {
                'title': 'URLs should use hyphens to separate words',
                'description': cls.get_url_with_underscore_message,
                'category': 'SEO'
            }
        }

    def validate(self):
        url = self.reviewer.page_url
        parsed_url = is_valid(url)
        path = parsed_url.path

        if '_' in path:
            self.add_violation(
                key='invalid.url_word_separator',
                value=url,
                points=10
            )
