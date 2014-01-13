#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.handlers import BaseHandler
from holmes.models import Violation, Review


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = Violation.get_most_common_violations(self.db, self.application.violation_definitions)

        result = []
        for item in violations:
            result.append({'name': item['title'], 'count': item['count']})

        self.write_json(result)
        self.finish()


class ViolationHandler(BaseHandler):
    @gen.coroutine
    def get(self, key_name):
        current_page = int(self.get_argument('current_page', 1))
        page_size = 100

        violations = self.application.violation_definitions
        violation_title = violations[key_name]['title']
        key_id = violations[key_name]['key'].id

        reviews = Review.get_by_violation_key_name(
            self.db,
            key_id,
            current_page=current_page,
            page_size=page_size)

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
            })

        self.write_json(json)
        self.finish()
