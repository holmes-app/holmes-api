#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator

REMOVE_HASH = re.compile('([#].*)$')


class LinkCrawlerValidator(Validator):
    def __init__(self, *args, **kw):
        super(LinkCrawlerValidator, self).__init__(*args, **kw)
        self.broken_links = set()
        self.moved_links = set()

    @classmethod
    def get_redirect_message(cls, value):
        return 'A link from your page to "%s" is using a 302 or 307 redirect. ' \
            'It passes 0%% of link juice (ranking power) and, in most cases, should not be used. ' \
            'Use 301 instead.' % (
                ', '.join(
                    [
                        '<a href="%s" target="_blank">Link #%s</a>' % (url, index)
                        for index, url in enumerate(value)
                    ]
                )
            )

    @classmethod
    def get_broken_link_message(cls, value):
        return 'This page contains broken links to %s ' \
            '(the urls failed to load or timed-out after 10 seconds). ' \
            'This can lead your site to lose rating with ' \
            'Search Engines and is misleading to users.' % (
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
            'link.broken': {
                'title': 'Broken link(s) found',
                'description': cls.get_broken_link_message,
                'category': 'HTTP'
            },
            'link.moved.temporarily': {
                'title': 'Moved Temporarily',
                'description': cls.get_redirect_message,
                'category': 'HTTP'
            }
        }

    def validate(self):
        links = self.get_links()

        total_score = float(self.reviewer.page_score)
        tax = total_score * float(self.reviewer.config.PAGE_SCORE_TAX_RATE)
        available_score = total_score - tax

        number_of_links = float(len(links)) or 1.0
        link_score = available_score / number_of_links

        for url, response in links:
            self.send_url(response.effective_url, link_score, response)

        if self.broken_links:
            self.add_violation(
                key='link.broken',
                value=self.broken_links,
                points=100 * len(self.broken_links)
            )

        if self.moved_links:
            self.add_violation(
                key='link.moved.temporarily',
                value=self.moved_links,
                points=100
            )

        self.flush()

    def flush(self, *args, **kw):
        super(LinkCrawlerValidator, self).flush(*args, **kw)
        self.broken_links = set()
        self.moved_links = set()

    def get_links(self):
        return self.review.data['page.links']

    def broken_link_violation(self, url, response):
        self.broken_links.add(url)

    def moved_link_violation(self, url, response):
        self.moved_links.add(url)
