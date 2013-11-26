#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.facters.links import REMOVE_HASH


class AnchorWithoutAnyTextValidator(Validator):

    def validate(self):
        links = self.get_links()

        links_with_empty_anchor = []

        for link in links:
            href = link.get('href').strip()
            href = REMOVE_HASH.sub('', href)

            if href and not link.text_content() and not link.findall('img'):
                is_absolute = self.is_absolute(href)
                if not is_absolute:
                    href = self.rebase(href)
                links_with_empty_anchor.append(href)

        if links_with_empty_anchor:
            data = []
            for index, href in enumerate(links_with_empty_anchor, start=1):
                data.append('<a href="%s" target="_blank">#%s</a>' % (
                    href, index))

            self.add_violation(
                key='empty.anchors',
                title='Empty anchor(s) found',
                description='Empty anchors are not good for Search Engines. '
                            'Empty anchors were found for links to: %s.' % (
                                ', '.join(data)),
                points=20 * len(links_with_empty_anchor)
            )

    def get_links(self):
        return self.review.data.get('page.all_links', None)
