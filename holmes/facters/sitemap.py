#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import re
import lxml.etree

from holmes.facters import Facter


ROBOTS_SITEMAP = re.compile('Sitemap:\s+(.*)')


class SitemapFacter(Facter):

    def get_facts(self):
        sitemaps = self.get_sitemaps()

        self.review.data['sitemap.data'] = {}
        self.review.data['sitemap.urls'] = set()
        self.review.data['sitemap.files'] = set()
        self.review.data['total.size.sitemap'] = 0
        self.review.data['total.size.sitemap.gzipped'] = 0

        self.add_fact(
            key='total.size.sitemap',
            value=0,
            unit='kb',
            title='Total Sitemap size'
        )

        self.add_fact(
            key='total.size.sitemap.gzipped',
            value=0,
            unit='kb',
            title='Total Sitemap size gzipped'
        )

        for sitemap in sitemaps:
            self.async_get(sitemap, self.handle_sitemap_loaded)

    def get_sitemaps(self):
        sitemaps = [self.rebase('/sitemap.xml')]

        if not self.review.data['robots.response']:
            return sitemaps

        return sitemaps + ROBOTS_SITEMAP.findall(self.review.data['robots.response'].text)

    def handle_sitemap_loaded(self, url, response):
        logging.debug('Got sitemap %s with status %s' % (url, response.status_code))
        self.review.data['sitemap.data'][url] = response

        namespaces = [
            ('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9'),
        ]

        if response.text is None or not response.text.strip():
            return

        size_sitemap = len(response.text) / 1024.0
        size_gzip = len(self.to_gzip(response.text)) / 1024.0

        self.review.facts['total.size.sitemap']['value'] += size_sitemap
        self.review.data['total.size.sitemap'] += size_sitemap

        self.review.facts['total.size.sitemap.gzipped']['value'] += size_gzip
        self.review.data['total.size.sitemap.gzipped'] += size_gzip

        tree = lxml.etree.fromstring(response.text)

        for sitemap in tree.xpath('//sm:sitemap | //sitemap', namespaces=namespaces):
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):
                url = loc.text.strip()
                self.review.data['sitemap.files'].add(url)
                self.async_get(url, self.handle_sitemap_loaded)

        for sitemap in tree.xpath('//sm:url | //url', namespaces=namespaces):
            for loc in sitemap.xpath('sm:loc | loc', namespaces=namespaces):
                url = loc.text.strip()
                self.review.data['sitemap.urls'].add(url)
                self.review.enqueue(url)
