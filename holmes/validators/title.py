#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class TitleValidator(Validator):
    def validate(self):
        title = self.reviewer.current_html.cssselect('title')

        if not title:
            self.add_violation(
                key='page.title.not_found',
                title='Page title not found.',
                description="Title was not found on %s" % self.reviewer.page_url,
                points=50
            )
            return

        if len(title) > 1:
            self.add_violation(
                key='page.title.multiple',
                title='To many titles.',
                description="Page %s has %d titles" % (self.reviewer.page_url, len(title)),
                points=50
            )
            return

        if not title[0].text:
            self.add_violation(
                key='page.title.not_found',
                title='Page title not found.',
                description="Title was not found on %s" % self.reviewer.page_url,
                points=50
            )
            return

        self.add_fact(
            key='page.title',
            value=title[0].text,
            title='Title'
        )

        if len(title[0].text) > self.reviewer.config.MAX_TITLE_SIZE:
            self.add_violation(
                key='page.title.exceed',
                title='Page title exceed maximum characters (%s).' % self.reviewer.config.MAX_TITLE_SIZE,
                description="Title tags to long may be truncated in the results",
                points=50
            )
