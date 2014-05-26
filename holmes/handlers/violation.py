#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen
from functools import partial

from holmes.handlers import BaseHandler
from holmes.models import Review, Violation, Domain


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = dict(self.girl.get('most_common_violations'))

        result = []
        for violation in self.application.violation_definitions.values():
            result.append({
                'name': self._(violation['title']),
                'key': violation['key'].name,
                'category': self._(violation['category']),
                'count': violations.get(violation['key'].name, 0),
            })

        self.write_json(result)
        self.finish()


class ViolationHandler(BaseHandler):

    @gen.coroutine
    def get(self, key_name):
        current_page = int(self.get_argument('current_page', 1))
        page_size = int(self.get_argument('page_size', 10))
        domain_filter = self.get_argument('domain_filter', None)
        page_filter = self.get_argument('page_filter', None)

        domain = None
        if domain_filter is not None:
            domain = Domain.get_domain_by_name(domain_filter, self.db)
            if not domain:
                self.set_status(404, self._('Domain %s not found') % domain_filter)
                self.finish()
                return

        violations = self.application.violation_definitions
        if key_name not in violations:
            self.set_status(404, self._('Invalid violation key %s') % key_name)
            self.finish()
            return

        violation_title = violations[key_name]['title']
        key_id = violations[key_name]['key'].id

        violation = yield self.application.search_provider.get_by_violation_key_name(
            key_id=key_id,
            current_page=current_page,
            page_size=page_size,
            domain=domain,
            page_filter=page_filter,
        )

        if 'reviewsCount' not in violation:
            if not domain and not page_filter:
                violation['reviewsCount'] = Review.count_by_violation_key_name(self.db, key_id)
            else:
                violation['reviewsCount'] = None

        violation['title'] = violation_title

        self.write_json(violation)
        self.finish()


class ViolationDomainsHandler(BaseHandler):

    def __init__(self, *args, **kw):
        super(ViolationDomainsHandler, self).__init__(*args, **kw)
        self.key_details_handler = {
            'blacklist.domains': partial(self.girl.get, 'blacklist_domain_count')
        }

    @gen.coroutine
    def get(self, key_name):
        violations = self.application.violation_definitions

        if key_name not in violations:
            self.set_status(404, self._('Invalid violation key %s') % key_name)
            return

        violation_title = violations[key_name]['title']
        violation_description = violations[key_name]['generic_description']
        violation_category = violations[key_name]['category']
        key_id = violations[key_name]['key'].id

        domains = Violation.get_by_key_id_group_by_domain(self.db, key_id)

        violation = {
            'title': self._(violation_title),
            'description': self._(violation_description),
            'category': self._(violation_category),
            'domains': [{'name': name, 'count': count} for (name, count) in domains],
            'total': sum(count for (name, count) in domains)
        }

        if key_name in self.key_details_handler:
            violation['details'] = self.key_details_handler[key_name]()

        self.write_json(violation)
        self.finish()


class ViolationsHandler(BaseHandler):
    def get(self):
        violations = self.application.violation_definitions

        json = []
        for key in violations.keys():
            violation = violations.get(key)
            json.append({
                'key_name': key,
                'title': self._(violation.get('title')),
                'category': self._(violation.get('category', None))
            })

        self.write_json(json)
        self.finish()
