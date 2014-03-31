#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
from tornado.gen import coroutine

from holmes.utils import get_status_code_title
from holmes.models import Request
from holmes.handlers import BaseHandler


class RequestDomainHandler(BaseHandler):

    @coroutine
    def get(self, domain_name, status_code):

        if not domain_name:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        if not status_code:
            self.set_status(404, 'Status code %s not found' % status_code)
            return

        if status_code == '200':
            self.set_status(403, 'Status code %s is not allowed' % status_code)
            return

        current_page = int(self.get_argument('current_page', 1))
        page_size = int(self.get_argument('page_size', 10))

        requests = Request.get_requests_by_status_code(
            domain_name,
            status_code,
            self.db,
            current_page=current_page,
            page_size=page_size
        )

        requests_count = Request.get_requests_by_status_count(
            domain_name,
            status_code,
            self.db
        )

        result = {
            'statusCodeTitle': get_status_code_title(status_code),
            'requestsCount': requests_count,
            'requests': []
        }

        for request in requests:
            result['requests'].append({
                'id': request.id,
                'url': request.url,
                'review_url': request.review_url,
                'completed_date': request.completed_date
            })

        self.write_json(result)


class LastRequestsHandler(BaseHandler):
    @coroutine
    def get(self):
        current_page = int(self.get_argument('current_page', 1))
        page_size = int(self.get_argument('page_size', 10))

        requests = Request.get_last_requests(
            self.db,
            current_page=current_page,
            page_size=page_size
        )

        requests_count = yield self.cache.get_requests_count()

        result = {'requestsCount': requests_count, 'requests': []}

        for request in requests:
            result['requests'].append(request.to_dict())

        self.write_json(result)


class RequestsInLastDayHandler(BaseHandler):
    @coroutine
    def get(self):
        from_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        requests = Request.get_requests_count_by_status_in_period_of_days(self.db, from_date=from_date)

        result = []
        for request in requests:
            result.append({
                'statusCode': request.status_code,
                'statusCodeTitle': get_status_code_title(request.status_code),  # FIXME: is it code or title??
                'count': request.count,
            })

        self.write_json(result)
