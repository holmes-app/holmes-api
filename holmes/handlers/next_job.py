#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import choice
from datetime import datetime, timedelta

from tornado import gen

from holmes.handlers import BaseHandler
from holmes.models.page import Page


class NextJobHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.REVIEW_EXPIRATION_IN_SECONDS)

        pages_in_need_of_review = self.db.query(Page.uuid, Page.url) \
            .filter(Page.last_review == None)[:200]

        if len(pages_in_need_of_review) == 0:
            pages_in_need_of_review = self.db.query(Page.uuid, Page.url) \
                .filter(
                    Page.last_review != None,
                    Page.last_review_date < dt
                ) \
                .order_by(Page.created_date)[:200]

            if len(pages_in_need_of_review) == 0:
                self.write('')
                self.finish()
                return

        has_lock = True

        for i in range(200):
            page = choice(pages_in_need_of_review)
            has_lock = yield self.cache.has_next_job_lock(page.url)

            if not has_lock:
                yield self.cache.lock_next_job(page.url)
                self.write_json({
                    'page': str(page.uuid),
                    'url': page.url
                })
                return

        self.write('')
        self.finish()
        return
