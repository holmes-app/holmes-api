#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator

REMOVE_HASH = re.compile('([#].*)$')


class LinkCrawlerValidator(Validator):
    def __init__(self, *args, **kw):
        super(LinkCrawlerValidator, self).__init__(*args, **kw)
        self.url_buffer = set()

    def validate(self):
        links = self.get_links()

        for url, response in links:
            self.send_url(url, response)

        self.flush()

    def test_url(self, url, response):
        status = response.status_code

        if status > 399:
            self.add_violation(
                key='broken.link',
                title='A link is broken',
                description=('A link from your page to "%s" is broken or the page failed to load in under 10 seconds. '
                    'This can lead your site to lose rating with Search Engines and is misleading to users.') % url,
                points=100
            )
            return False

        if status == 302 or status == 307:
            self.add_violation(
                key='moved.temporarily',
                title='Moved Temporarily',
                description='A link from you page to "%s" is using a %d redirect. '
                'It passes 0%% of link juice (ranking power) and, in most cases, should not be used. '
                'Use 301 instead. ' % (url, status),
                points=100
            )
            return False

        if response.url.rstrip('/') != url.rstrip('/'):
            return False

        return True

    def send_url(self, url, response):
        if self.test_url(url, response):
            self.url_buffer.add(url)

        if len(self.url_buffer) > self.config.MAX_ENQUEUE_BUFFER_LENGTH:
            self.flush()

    def flush(self):
        if not self.url_buffer:
            return

        self.enqueue(*self.url_buffer)
        self.url_buffer = []

    def get_links(self):
        return self.review.data['page.links']
