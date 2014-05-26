#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from tornado import gen
from ujson import loads

from holmes.models import Page, Review
from holmes.handlers import BaseHandler


class PageHandler(BaseHandler):
    def get(self, uuid=''):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, self._('Page UUID [%s] not found') % uuid)
            return

        page_json = {
            "uuid": str(page.uuid),
            "url": page.url
        }

        self.write(page_json)

    @gen.coroutine
    def post(self):
        post_data = loads(self.request.body)
        url = post_data['url']
        score = float(post_data.get('score', self.application.config.DEFAULT_PAGE_SCORE))

        result = yield Page.add_page(
            self.db,
            self.application.cache,
            url,
            score,
            self.application.http_client.fetch,
            self.application.event_bus.publish,
            self.application.config,
            self.application.girl
        )

        created, url, result = result

        if not created and result['reason'] == 'invalid_url':
            self.set_status(400, self._('Invalid url [%s]') % url)
            self.write_json({
                'reason': 'invalid_url',
                'url': url,
                'status': result['status'],
                'details': result['details']
            })
            return

        if not created and result['reason'] == 'redirect':
            self.set_status(400, self._('Supplied URL is a redirect [%s]') % url)
            self.write_json({
                'reason': 'redirect',
                'url': url,
                'effectiveUrl': result['effectiveUrl']
            })
            return

        self.write(str(result))
        self.finish()


class PageReviewsHandler(BaseHandler):

    def get(self, uuid='', limit=10):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, self._('Page UUID [%s] not found') % uuid)
            return

        reviews = self.db.query(Review) \
            .filter(Review.page == page) \
            .filter(Review.is_complete == True) \
            .order_by(Review.completed_date.desc())[:limit]

        result = []
        for review in reviews:
            result.append({
                'uuid': str(review.uuid),
                'completedAt': review.completed_date,
                'violationCount': review.violation_count
            })

        self.write_json(result)


class PageViolationsPerDayHandler(BaseHandler):

    def get(self, uuid):
        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, self._('Page UUID [%s] not found') % uuid)
            return

        violations_per_day = page.get_violations_per_day(self.db)

        page_json = {
            "violations": violations_per_day
        }

        self.write_json(page_json)


class NextJobHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        get_next_job_list = Page.get_next_job_list(
            self.db,
            self.application.config.REVIEW_EXPIRATION_IN_SECONDS,
            current_page=int(self.get_argument('current_page', 1)),
            page_size=int(self.get_argument('page_size', 10)),
            domain_filter=self.get_argument('domain_filter', None)
        )

        pages = []
        for item in get_next_job_list:
            pages.append({
                'uuid': item.uuid,
                'url': item.url,
            })

        self.write_json({'pages': pages})
