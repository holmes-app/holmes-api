#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class GoogleAnalyticsValidator(Validator):

    @classmethod
    def get_analytics_message(cls, value=None):
        return 'This page should include a Google Analytics.'

    @classmethod
    def get_account_message(cls, value=None):
        return 'This page should include a Google Analytics account.'

    @classmethod
    def get_domain_message(cls, value=None):
        return 'This page should include a Google Analytics domain.'

    @classmethod
    def get_violation_definitions(cls):
        return {
            'google_analytics.not_found': {
                'title': 'Google Analytics not found',
                'description': cls.get_analytics_message,
                'category': 'SEO'
            },
            'google_analytics.account.not_found': {
                'title': 'Google Analytics account not found',
                'description': cls.get_account_message,
                'category': 'SEO'
            },
            'google_analytics.domain.not_found': {
                'title': 'Google Analytics domain not found',
                'description': cls.get_domain_message,
                'category': 'SEO'
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
