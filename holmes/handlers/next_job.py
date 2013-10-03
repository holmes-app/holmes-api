#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from tornado.web import RequestHandler
from tornado import gen
from ujson import dumps

from holmes.models.page import Page
from holmes.models.review import Review


class NextJobHandler(RequestHandler):

    @gen.coroutine
    def post(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.REVIEW_EXPIRATION_IN_SECONDS)

        pages_in_need_of_review = yield Page.objects.filter(
            last_review__is_null=False,
            last_review_date__is_null=False,
            last_review_date__lt=dt
        ).find_all()

        if len(pages_in_need_of_review) == 0:
            self.write("")
            self.finish()
            return

        page = pages_in_need_of_review[0]

        review = yield Review.objects.create(
            page=page,
            facts=[],
            violations=[]
        )

        self.write(dumps({
            "page": str(page.uuid),
            "review": str(review.uuid),
            "url": page.url
        }))

        self.finish()
