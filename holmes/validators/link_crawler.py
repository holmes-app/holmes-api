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

    def validate(self):
        links = self.get_links()

        for url, response in links:
            self.send_url(response.effective_url, response)

        if self.broken_links:
            data = []
            for index, url in enumerate(self.broken_links, start=1):
                data.append('<a href="%s" target="_blank">Link #%s</a>' % (url, index))

            self.add_violation(
                key='broken.link',
                title='A link is broken',
                description=('A link from your page to "%s" is broken or the '
                             'page failed to load in under 10 seconds. '
                             'This can lead your site to lose rating with '
                             'Search Engines and is misleading to users.') % (', '.join(data)),
                points=100 * len(self.broken_links)
            )

        if self.moved_links:
            data = []
            for index, url in enumerate(self.moved_links, start=1):
                data.append('<a href="%s" target="_blank">Link #%s</a>' % (url, index))

            self.add_violation(
                key='moved.temporarily',
                title='Moved Temporarily',
                description='A link from your page to "%s" is using a 302 or 307 redirect. '
                'It passes 0%% of link juice (ranking power) and, in most cases, should not be used. '
                'Use 301 instead. ' % (', '.join(data)),
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
