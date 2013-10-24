#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from tornado.web import RequestHandler
from tornado import gen
from ujson import dumps
from motorengine import Q

from holmes.models.page import Page
from holmes.models.review import Review


class NextJobHandler(RequestHandler):

    @gen.coroutine
    def post(self):
        dt = datetime.now() - timedelta(seconds=self.application.config.REVIEW_EXPIRATION_IN_SECONDS)
        query = Q(last_review__is_null=True) | (
            Q(last_review__is_null=False, last_review_date__is_null=False, last_review_date__lt=dt)
        )
        pages_in_need_of_review = yield Page.objects.filter(query) \
                                                    .order_by('added_date').find_all()

        if len(pages_in_need_of_review) == 0:
            self.write('')
            self.finish()
            return

        page = pages_in_need_of_review[0]

        review = yield Review.objects.create(
            page=page,
            facts=[],
            violations=[]
        )

        page.last_review = review
        yield page.save()

        self.write(dumps({
            'page': str(page.uuid),
            'review': str(review.uuid),
            'url': page.url
        }))

        self.finish()
