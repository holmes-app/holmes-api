#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class GoogleAnalyticsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'google_analytics.not_found': {
                'title': _('Google Analytics not found'),
                'description': _(
                    'This page should include a Google Analytics.'),
                'category': _('SEO'),
                'generic_description': _(
                    'Google Analytics script is important to measure '
                    'various kinds of statistics of the page. It\'s a SEO '
                    'violation an ausence of this script.'
                )
            },
            'google_analytics.account.not_found': {
                'title': _('Google Analytics account not found'),
                'description': _(
                    'This page should include a Google Analytics account.'),
                'category': _('SEO'),
                'generic_description': _(
                    'Google Analytics script is important to measure '
                    'various kinds of statistics of the page. The '
                    'configuration of the script needs an account '
                    'to log in. Not founding this information may '
                    'cause errors to log the statistics in the Google API.'
                )
            },
            'google_analytics.domain.not_found': {
                'title': _('Google Analytics domain not found'),
                'description': _(
                    'This page should include a Google Analytics domain.'),
                'category': _('SEO'),
                'generic_description': _(
                    'Google Analytics script is important to measure '
                    'various kinds of statistics of the page. The '
                    'configuration of the script needs a domain '
                    'information to work well.'
                )
            }
        }

    def validate(self):
        google_analytics = self.get_analytics()

        if not google_analytics:
            self.add_violation(
                key='google_analytics.not_found',
                value=None,
                points=100
            )
            return

        for account, domain in google_analytics:
            if not account:
                self.add_violation(
                    key='google_analytics.account.not_found',
                    value=None,
                    points=50
                )

            if not domain:
                self.add_violation(
                    key='google_analytics.domain.not_found',
                    value=None,
                    points=50
                )

    def get_analytics(self):
        return self.review.data.get('page.google_analytics', None)
