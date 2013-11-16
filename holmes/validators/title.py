#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class TitleValidator(Validator):
    def required_facters(self):
        return ("holmes.facters.title.Title", )

    def validate(self):
        title_count = self.review.data.get('page.title.count', 0)
        title = self.review.facts.get('page.title', None)

        if not title_count:
            self.add_violation(
                key='page.title.not_found',
                title='Page title not found.',
                description="Title was not found on %s" % self.reviewer.page_url,
                points=50
            )
            return

        if title_count > 1:
            self.add_violation(
                key='page.title.multiple',
                title='To many titles.',
                description="Page %s has %d titles" % (self.reviewer.page_url, len(title)),
                points=50
            )
            return

        if not title:
            self.add_violation(
                key='page.title.not_found',
                title='Page title not found.',
                description="Title was not found on %s" % self.reviewer.page_url,
                points=50
            )
            return

        if 'page.title.count' in self.review.facts:
            del self.review.facts['page.title.count']
