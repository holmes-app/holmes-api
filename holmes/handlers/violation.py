#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.handlers import BaseHandler
from holmes.models import Violation


class MostCommonViolationsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        violations = Violation.get_most_common_violations(self.db, self.application.violation_definitions)

        result = []
        for item in violations:
            result.append({'name': item['title'], 'count': item['count']})

        self.write_json(result)
        self.finish()
