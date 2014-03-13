#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.handlers import BaseHandler
from holmes.models import Review, Violation


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = yield self.cache.get_most_common_violations(
            self.application.violation_definitions,
            self.application.config.get('MOST_COMMON_VIOLATIONS_SAMPLE_LIMIT')
        )

        result = []
        for item in violations:
            result.append({
                'name': item['title'],
                'key': item['key'],
                'category': item['category'],
                'count': item['count']
            })

        s1 = set(self.application.violation_definitions.keys())
        s2 = set((x.get('key') for x in result))

        diff = s1 - s2
        for item in diff:
            violation = self.application.violation_definitions[item]
            result.append({
                'name': violation['title'],
                'key': violation['key'].name,
                'category': violation['category'],
                'count': 1
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

        reviews_count = Review.count_by_violation_key_name(
            self.db,
            key_id,
            domain_filter=domain_filter,
            page_filter=page_filter
        )

        reviews_data = []
        for item in reviews:
            reviews_data.append({
                'uuid': item.review_uuid,
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
    @gen.coroutine
    def get(self, key_name):
        violations = self.application.violation_definitions
        violation_title = violations[key_name]['title']
        key_id = violations[key_name]['key'].id

        domains = Violation.get_by_key_id_group_by_domain(self.db, key_id)

        violation = {
            'title': violation_title,
            'domains': [{'name': name, 'count': count} for (name, count) in domains],
            'total': sum(count for (name, count) in domains)
        }

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
