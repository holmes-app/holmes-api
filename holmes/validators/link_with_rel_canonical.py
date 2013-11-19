#!/usr/bin/python
# -*- coding: utf-8 -*-

from urlparse import urlparse

from holmes.validators.base import Validator


class LinkWithRelCanonicalValidator(Validator):

    def validate(self):
        if not self.config.FORCE_CANONICAL:
            # Only pages with query string parameters
            if self.page_url:
                if not urlparse(self.page_url).query:
                    return

        head = self.get_head()
        canonical = [item for item in head if item.get('rel') == 'canonical']

        if not canonical:
            url = 'https://support.google.com/webmasters/answer/139394?hl=en'

            self.add_violation(
                key='absent.meta.canonical',
                title='Link with rel="canonical" not found',
                description='As can be seen in this page <a href="%s">About '
                            'rel="canonical"</a>, it\'s a good practice to '
                            'include rel="canonical" urls in the pages for '
                            'your website.' % (url),
                points=30
            )

    def get_head(self):
        return self.review.data.get('page.head', None)
