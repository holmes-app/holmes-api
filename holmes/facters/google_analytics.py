#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.facters import Facter


class GoogleAnalyticsFacter(Facter):

    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.google_analytics': {
                'title': 'Google Analytics',
                'description': lambda value: list(value),
                'unit': 'google-analytics',
                'category': 'SEO',
            }
        }

    def get_facts(self):
        self.review.data['page.google_analytics'] = set()

        script_data = self.get_script_data()

        account_regex = "_?setAccount[^,]*,[^']*'([^']*)'"
        domain_regex = "-?setDomainName[^,]*,[^']*'([^']*)'"

        analytics_re = re.compile(
            r"%s(.*?)%s" % (account_regex, domain_regex),
            re.MULTILINE | re.DOTALL)

        for i in script_data:
            if i.text:
                analytics_data = analytics_re.findall(i.text)
                for account, _, domain in analytics_data:
                    self.review.data['page.google_analytics'].add(
                        (account, domain)
                    )

        if self.review.data['page.google_analytics']:
            self.add_fact(
                key='page.google_analytics',
                value=self.review.data['page.google_analytics'],
            )

    def get_script_data(self):
        return self.reviewer.current_html.cssselect('script')
