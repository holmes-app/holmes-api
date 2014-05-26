#!/usr/bin/python
# -*- coding: utf-8 -*-

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
        requests = Request.get_last_requests(
            self.db,
            current_page=int(self.get_argument('current_page', 1)),
            page_size=int(self.get_argument('page_size', 10)),
            domain_filter=self.get_argument('domain_filter', None),
            status_code_filter=self.get_argument('status_code_filter', None)
        )

        self.write_json(
            {'requests': [request.to_dict() for request in requests]}
        )


class FailedResponsesHandler(BaseHandler):
    @coroutine
    def get(self):
        requests = self.girl.get('failed_responses_count')
        domain_filter = self.get_argument('domain_filter', None)

        if not domain_filter:
            domain_filter = '_all'

        result = []
        if domain_filter in requests:
            for status_code, count in requests[domain_filter]:
                result.append({
                    'statusCode': status_code,
                    'statusCodeTitle': get_status_code_title(status_code),
                    'count': count,
                })

        self.write_json(result)


class LastRequestsStatusCodeHandler(BaseHandler):
    @coroutine
    def get(self):
        status_code = Request.get_all_status_code(self.db)

        self.write_json(status_code)
