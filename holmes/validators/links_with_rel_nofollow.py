#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import get_domain_from_url
from holmes.validators.base import Validator


class LinkWithRelNofollowValidator(Validator):

    def validate(self):

        links = self.get_links()

        page_domain, domain_url = get_domain_from_url(self.review.page_url)

        rel_nofollow = []

        for link in links:
            href = link.get('href')
            link_domain, link_domain_url = get_domain_from_url(href)

            if link.get('rel') == 'nofollow' and page_domain == link_domain:
                rel_nofollow.append(link)

        if rel_nofollow:
            data = []
            for index, link in enumerate(rel_nofollow, start=1):
                data.append('<a href="%s" target="_blank">#%s</a>' % (
                    link.get('href'), index))

                self.add_violation(
                    key='invalid.links.nofollow',
                    title='Links with rel="nofollow"',
                    description='Links with rel="nofollow" to the same '
                                'domain as the page make it harder for search '
                                'engines to crawl the website. Links with '
                                'rel="nofollow" were found for hrefs (%s).' % (
                                    ', '.join(data)),
                    points=10 * len(rel_nofollow)
                )

    def get_links(self):
        return self.review.data.get('page.all_links', None)
