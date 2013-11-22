#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class AnchorWithoutAnyTextValidator(Validator):

    def validate(self):
        links = self.get_links()

        links_with_empty_anchor = []

        for link in links:
            if not link.text:
                links_with_empty_anchor.append(link)

        if links_with_empty_anchor:
            data = []
            for index, link in enumerate(links_with_empty_anchor, start=1):
                data.append('<a href="%s" target="_blank">#%s</a>' % (
                    link.get('href'), index))

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
