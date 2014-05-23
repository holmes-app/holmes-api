#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import get_domain_from_url, is_valid
from holmes.validators.base import Validator
from holmes.utils import _


class BlackListValidator(Validator):
    @classmethod
    def get_blacklist_parsed_value(cls, value):
        return ', '.join([
            '<a href="%s" target="_blank">Link #%s</a>' % (url, index)
            for index, url in enumerate(value)
        ])

    @classmethod
    def get_violation_definitions(cls):
        return {
            'blacklist.domains': {
                'title': _('Domain Blacklist'),
                'description': _('Some links are blacklisted: %s'),
                'value_parser': cls.get_blacklist_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Detected domain blacklisted hyperlinks. '
                    'Links with this violation are those that have anchors '
                    'to websites added in Holmes\'s Black List configuration.'
                ),
                'unit': 'list'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'blacklist.domains': {
                'value': config.BLACKLIST_DOMAIN,
                'description': config.get_description('BLACKLIST_DOMAIN')
            }
        }

    def validate(self):
        blacklist_domains = self.get_violation_pref('blacklist.domains')

        domains = []

        links = self.get_links()

        for link in links:
            href = link.get('href')

            if not is_valid(href):
                continue

            link_domain, link_domain_url = get_domain_from_url(href)
            if link_domain in blacklist_domains:
                domains.append(href)

        if domains:
            self.add_violation(
                key='blacklist.domains',
                value=domains,
                points=100 * len(domains)
            )

    def get_links(self):
        return self.review.data.get('page.all_links', None)
