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

    @classmethod
    def get_violation_definitions(cls):
        return {
            'sitemap.not_found': {
                'title': 'SiteMap file not found',
                'description': lambda value: "The sitemap file was not found at '%s'." % value,
                'category': 'SEO',
                'generic_description': (
                    'Validates the absent of a SiteMap file on the page.'
                )
            },
            'sitemap.empty': {
                'title': 'SiteMap file is empty',
                'description': lambda value: "The sitemap file was found at '%s', but was empty." % value,
                'category': 'Semantics',
                'generic_description': 'Validates the emptiness of site\'s SiteMap file.'
            },
            'total.size.sitemap': {
                'title': 'SiteMap file is too big',
                'description': lambda value: "The sitemap file was found at '%s', but was too big (%.2fMB)." % (
                    value['url'], value['size']
                ),
                'category': 'Performance',
                'generic_description': 'Validates the size of site\'s SiteMap file.'
            },
            'total.links.sitemap': {
                'title': 'SiteMap file contains too many links',
                'description': lambda value: "The sitemap file was found at '%s', but contained too many links (%d). Maybe splitting it would help?" % (
                    value['url'], value['links']
                ),
                'category': 'SEO',
                'generic_description': (
                    'Validates the number of links containing in the site\'s SiteMap file. '
                    'This limit is configurable on Holmes configuration.'
                )
            },
            'sitemap.links.not_encoded': {
                'title': 'SiteMap file contains unencoded links',
                'description': lambda value: "The sitemap file was found at '%s', but contains unencoded links (%s)." % (
                    value['url'], value['links']
                ),
                'category': 'Semantics',
                'generic_description': (
                    'Validates the value of site\'s SiteMap file links.'
                )
            }
        }

    def validate(self):
        if not self.reviewer.is_root():
            return

        for sitemap, size in self.review.data['sitemap.files.size'].items():
            response = self.review.data['sitemap.data'][sitemap]

            if response.status_code > 399:
                self.add_violation(
                    key='sitemap.not_found',
                    value=sitemap,
                    points=100
                )
                return

            if not response.text.strip():
                self.add_violation(
                    key='sitemap.empty',
                    value=sitemap,
                    points=100
                )
                return

            size_mb = (size / 1024.0)
            urls_count = self.review.data['sitemap.files.urls'][sitemap]
            not_encoded_links = 0

            if size_mb > self.MAX_SITEMAP_SIZE:
                self.add_violation(
                    key='total.size.sitemap',
                    value={
                        'url': sitemap,
                        'size': size_mb
                    },
                    points=10
                )

            if urls_count > self.MAX_LINKS_SITEMAP:
                self.add_violation(
                    key='total.links.sitemap',
                    value={
                        'url': sitemap,
                        'links': urls_count
                    },
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
                except (UnicodeEncodeError, UnicodeDecodeError):
                    encoded = False

                relative = HTML_ENTITIES.sub('', relative)
                encoded = encoded and not INVALID_CHARS.findall(relative)

                if not encoded:
                    not_encoded_links += 1

                self.send_url(url, self.reviewer.page_score / float(urls_count), response)

            if not_encoded_links > 0:
                self.add_violation(
                    key='sitemap.links.not_encoded',
                    value={
                        'url': sitemap,
                        'links': not_encoded_links
                    },
                    points=10
                )

        self.flush()
