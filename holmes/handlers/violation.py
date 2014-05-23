#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen
from functools import partial

from holmes.handlers import BaseHandler
from holmes.models import Review, Violation


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = dict(self.girl.get('most_common_violations'))

        result = []
        for violation in self.application.violation_definitions.values():
            result.append({
                'name': violation['title'],
                'key': violation['key'].name,
                'category': violation['category'],
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

        violations = self.application.violation_definitions
        if key_name not in violations:
            self.set_status(404, 'Invalid violation key %s' % key_name)
            return

        violation_title = violations[key_name]['title']
        key_id = violations[key_name]['key'].id

        reviews = Review.get_by_violation_key_name(
            self.db,
            key_id,
            current_page=current_page,
            page_size=page_size,
            domain_filter=domain_filter,
            page_filter=page_filter,
        )

        if domain_filter or page_filter:
            reviews_count = None
        else:
            reviews_count = Review.count_by_violation_key_name(self.db, key_id)

        reviews_data = []
        for item in reviews:
            reviews_data.append({
                'uuid': item.review_uuid,
                'domain': item.domain_name,
                'page': {
                    'uuid': item.page_uuid,
                    'url': item.url,
                    'completedAt': item.completed_date
                }
            })

        violation = {
            'title': violation_title,
            'reviews': reviews_data,
            'reviewsCount': reviews_count
        }

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
            self.set_status(404, 'Invalid violation key %s' % key_name)
            return

        violation_title = violations[key_name]['title']
        key_id = violations[key_name]['key'].id

        domains = Violation.get_by_key_id_group_by_domain(self.db, key_id)

        violation = {
            'title': violation_title,
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
                'title': violation.get('title'),
                'category': violation.get('category', None)
            })

        self.write_json(json)
        self.finish()
