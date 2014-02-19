#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import get_domain_from_url, is_valid
from holmes.validators.base import Validator


class BlackListValidator(Validator):
    @classmethod
    def get_blacklist_message(cls, value):
        return 'Some links are blacklisted: %s' % (
            ', '.join(
                    [
                        '<a href="%s" target="_blank">Link #%s</a>' % (url, index)
                        for index, url in enumerate(value)
                    ]
                )
            )

    @classmethod
    def get_violation_definitions(cls):
        return {
            'blacklist.domains': {
                'title': 'Domain Blacklist',
                'description': cls.get_blacklist_message,
                'category': 'SEO'
            }
        }

    def validate(self):
        domains = []

        links = self.get_links()

        for link in links:
            href = link.get('href')

            if not is_valid(href):
                continue

            link_domain, link_domain_url = get_domain_from_url(href)
            if link_domain in self.reviewer.config.BLACKLIST_DOMAIN:
                domains.append(href)

        if domains:
            self.add_violation(
                key='blacklist.domains',
                value=domains,
                points=100 * len(domains)
            )

    def get_links(self):
        return self.review.data.get('page.all_links', None)
