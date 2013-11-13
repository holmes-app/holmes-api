#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import choice
from datetime import datetime, timedelta

from tornado import gen
from motorengine import Q
from sqlalchemy import or_, and_

from holmes.handlers import BaseHandler
from holmes.models.page import Page
from holmes.models.review import Review


class NextJobHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.REVIEW_EXPIRATION_IN_SECONDS)
        timed_out = datetime.now() - timedelta(seconds=self.application.config.ZOMBIE_WORKER_TIME)

        pages_in_need_of_review = self.db.query(Page) \
            .filter(or_(
                Page.last_review == None,
                and_(
                    Page.last_review_date != None,
                    Page.last_review_date < dt
                ),
                and_(
                    Page.last_review_date == None,
                    Page.last_review_started_date != None,
                    Page.last_review_started_date < timed_out
                )
            )) \
            .order_by(Page.created_date) \
            .all()

        if len(pages_in_need_of_review) == 0:
            self.write('')
            self.finish()
            return

        page = choice(pages_in_need_of_review)

        if page.last_review and page.last_review_started_date and page.last_review_started_date < timed_out:
            page.last_review.failure_message = "Timed out after %.0f seconds." % (
                (datetime.now() - page.last_review_started_date).total_seconds()
            )
            self.db.flush()

        review = Review(
            domain=page.domain,
            page=page
        )

        self.db.flush()

        page.last_review = review
        page.last_review_started_date = datetime.now()

        self.db.flush()

        self.write_json({
            'page': str(page.uuid),
            'review': str(review.uuid),
            'url': page.url
        })
