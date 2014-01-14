#!/usr/bin/python
# -*- coding: utf-8 -*-

import email.utils as eut
from datetime import datetime

from holmes.facters import Facter


class LastModifiedFacter(Facter):

    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.last_modified': {
                'title': 'Last-Modified',
                'description': lambda value: value
            }
        }

    def get_facts(self):
        last_modified = self.get_last_modified()

        if not last_modified:
            return

        self.review.data['page.last_modified'] = last_modified
        self.add_fact(key='page.last_modified', value=last_modified)

    def get_last_modified(self):
        last_modified = None

        headers = self.reviewer.current.headers

        if 'Last-Modified' in headers:
            lt = headers['Last-Modified']
            last_modified = datetime(*eut.parsedate(lt)[:6])

        return last_modified
