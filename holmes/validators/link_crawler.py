#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator
from holmes.utils import get_domain_from_url

REMOVE_HASH = re.compile('([#].*)$')


class LinkCrawlerValidator(Validator):
    def __init__(self, *args, **kw):
        super(LinkCrawlerValidator, self).__init__(*args, **kw)
        self.url_buffer = []

    def looks_like_image(self, url):
        image_types = ['png', 'webp', 'gif', 'jpg', 'jpeg']
        for image_type in image_types:
            if url.endswith(image_type):
                return True

        return False

    def validate(self):
        links = self.get_links()
        num_links = 0

        for link in links:
            url = link.get('href')
            url = REMOVE_HASH.sub('', url)

            if not url:
                continue

            if self.looks_like_image(url):
                continue

            is_absolute = self.is_absolute(url)

            if not is_absolute:
                url = self.rebase(url)
                self.test_url(url)
                self.send_url(url)
                num_links += 1
            else:
                domain, domain_url = get_domain_from_url(url)
                if domain in self.page_url:
                    self.test_url(url)
                    self.send_url(url)
                num_links += 1

        self.add_fact(
            key='total.number.links',
            value=num_links
        )

        self.flush()

    def test_url(self, url):
        status = self.get_status_code(url)

        if status > 399:
            self.add_violation(
                key='broken.link',
                title='A link is broken',
                description=('A link from your page to "%s" is broken or the page failed to load in under 3 seconds. '
                    'This can lead your site to lose rating with Search Engines and is misleading to users.') % url,
                points=100
            )

        if status == 302 or status == 307:
            self.add_violation(
                key='moved.temporarily',
                title='Moved Temporarily',
                description='A link from you page to "%s" is using a %d redirect. '
                'It passes 0%% of link juice (ranking power) and, in most cases, should not be used. '
                'Use 301 instead. ' % (status, url),
                points=100
            )

    def send_url(self, url):
        self.url_buffer.append(url)

        if len(self.url_buffer) > self.config.MAX_ENQUEUE_BUFFER_LENGTH:
            self.flush()

    def flush(self):
        if not self.url_buffer:
            return

        self.enqueue(*self.url_buffer)
        self.url_buffer = []

    def get_links(self):
        return self.reviewer.current['html'].cssselect('a[href]')
