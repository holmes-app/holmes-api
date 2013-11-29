#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator

URL_RE = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?P<relative>(?:/?|[/?]\S+))$', re.IGNORECASE)

HTML_ENTITIES = re.compile(r'(&amp;|&apos;|&quot;|&gt;|&lt;)')
INVALID_CHARS = re.compile(r'(&|\'|"|>|<)')


class SitemapValidator(Validator):
    MAX_SITEMAP_SIZE = 10  # 10 MB
    MAX_LINKS_SITEMAP = 50000

    def validate(self):
        if not self.reviewer.is_root():
            return

        for sitemap, size in self.review.data['sitemap.files.size'].items():
            response = self.review.data['sitemap.data'][sitemap]

            if response.status_code > 399:
                self.add_violation(
                    key='sitemaps.not_found',
                    title='Sitemaps not found',
                    description='',
                    points=100
                )
                return

            if not response.text.strip():
                self.add_violation(
                    key='sitemaps.empty',
                    title='Empty sitemaps file',
                    description='',
                    points=100
                )
                return

            size_mb = (size / 1024.0)
            urls_count = self.review.data['sitemap.files.urls'][sitemap]
            not_encoded_links = 0

            if size_mb > self.MAX_SITEMAP_SIZE:
                self.add_violation(
                    key='total.size.sitemap',
                    title='Sitemap size in MB is too big.',
                    description='There\'s %.2fMB of Sitemap in the %s file. '
                                'Sitemap files should not exceed %s MB.'
                                % (size_mb, sitemap, self.MAX_SITEMAP_SIZE),
                    points=10
                )

            if urls_count > self.MAX_LINKS_SITEMAP:
                self.add_violation(
                    key='total.links.sitemap',
                    title='Many links in a single sitemap.',
                    description='There\'s %d links in the %s sitemap. '
                                'Sitemap links should not exceed %s links.'
                                % (urls_count, sitemap, self.MAX_LINKS_SITEMAP),
                    points=10
                )

            for url in self.review.data['sitemap.urls'][sitemap]:
                match = URL_RE.match(url)

                if not match:
                    continue

                parse = match.groupdict()
                relative = parse['relative']
                encoded = True

                try:
                    str(relative).encode('utf-8')
                except UnicodeEncodeError:
                    encoded = False

                relative = HTML_ENTITIES.sub('', relative)
                encoded = encoded and not INVALID_CHARS.findall(relative)

                if not encoded:
                    not_encoded_links += 1

                self.send_url(response.effective_url, response)

            if not_encoded_links > 0:
                self.add_violation(
                    key='sitemaps.links.not_encoded',
                    title='Url in sitemap is not encoded',
                    description='There\'s %d not encoded links in the %s sitemap.'
                                % (not_encoded_links, sitemap),
                    points=10
                )

        self.flush()
