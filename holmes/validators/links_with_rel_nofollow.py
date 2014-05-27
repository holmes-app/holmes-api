#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import get_domain_from_url, is_valid, _
from holmes.validators.base import Validator


class LinkWithRelNofollowValidator(Validator):
    @classmethod
    def get_links_nofollow_parsed_value(cls, value):
        return {'links': ', '.join([
            '<a href="%s" target="_blank">#%s</a>' % (link, index)
            for index, link in enumerate(value)
        ])}

    @classmethod
    def get_violation_definitions(cls):
        return {
            'invalid.links.nofollow': {
                'title': _('Links with rel="nofollow"'),
                'description': _(
                    'Links with rel="nofollow" to the same '
                    'domain as the page make it harder for search '
                    'engines to crawl the website. Links with '
                    'rel="nofollow" were found for hrefs (%(links)s).'),
                'value_parser': cls.get_links_nofollow_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Validates links with rel="nofollow", this whos links to '
                    'the same domain as the page make it harder for search '
                    'engines to crawl the website.'
                )
            }
        }

    def validate(self):

        links = self.get_links()

        page_domain, domain_url = get_domain_from_url(self.review.page_url)

        rel_nofollow = []

        for link in links:
            href = link.get('href')

            if not is_valid(href):
                continue

            link_domain, link_domain_url = get_domain_from_url(href)

            if link.get('rel') == 'nofollow' and page_domain == link_domain:
                rel_nofollow.append(href)

        if rel_nofollow:
            self.add_violation(
                key='invalid.links.nofollow',
                value=rel_nofollow,
                points=10 * len(rel_nofollow)
            )

    def get_links(self):
        return self.review.data.get('page.all_links', None)
