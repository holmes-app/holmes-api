#!/usr/bin/python
# -*- coding: utf-8 -*-

import re

from holmes.validators.base import Validator
from holmes.utils import _

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
                'title': _('SiteMap file not found'),
                'description': _("The sitemap file was not found at '%s'."),
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the absent of a SiteMap file on the page.')
            },
            'sitemap.empty': {
                'title': _('SiteMap file is empty'),
                'description': _(
                    "The sitemap file was found at '%s', but was empty."),
                'category': _('Semantics'),
                'generic_description': _(
                    'Validates the emptiness of site\'s SiteMap file.')
            },
            'total.size.sitemap': {
                'title': _('SiteMap file is too big'),
                'description': _(
                    "The sitemap file was found at '%(url)s', but was "
                    "too big (%(size).2fMB)."),
                'category': _('Performance'),
                'generic_description': _(
                    'Validates the size of site\'s SiteMap file.')
            },
            'total.links.sitemap': {
                'title': _('SiteMap file contains too many links'),
                'description': _(
                    "The sitemap file was found at '%(url)s', but contained "
                    "too many links (%(links)d). Maybe splitting it would "
                    "help?"),
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the number of links containing in the site\'s '
                    'SiteMap file. This limit is configurable on Holmes '
                    'configuration.'
                )
            },
            'sitemap.links.not_encoded': {
                'title': _('SiteMap file contains unencoded links'),
                'description': _(
                    "The sitemap file was found at '%(url)s', but contains "
                    "unencoded links (%(links)s)."),
                'category': _('Semantics'),
                'generic_description': _(
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
