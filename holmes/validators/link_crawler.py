#!/usr/bin/python
# -*- coding: utf-8 -*-

import urlparse
import re

from holmes.validators.base import Validator
from holmes.utils import get_domain_from_url

REMOVE_HASH = re.compile('([#].*)$')


class LinkCrawlerValidator(Validator):
    def __init__(self, *args, **kw):
        super(LinkCrawlerValidator, self).__init__(*args, **kw)
        self.url_buffer = []

    def is_absolute(self, url):
        return bool(urlparse.urlparse(url).scheme)

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
                self.send_url(url=urlparse.urljoin(self.page_url.rstrip('/'), url.lstrip('/')))
                num_links += 1
            else:
                domain, domain_url = get_domain_from_url(url)
                if domain in url:
                    self.send_url(url)
                    num_links += 1

        self.add_fact(
            key='total.links',
            value=num_links
        )

        self.flush()

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
