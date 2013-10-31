#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import choice
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
        timed_out = datetime.now() - timedelta(seconds=self.application.config.ZOMBIE_WORKER_TIME)

        query = Q(last_review__is_null=True) | (
            Q(last_review_date__is_null=False, last_review_date__lt=dt)
        ) | (
            Q(last_review_date__is_null=True, last_review_started_date__is_null=False, last_review_started_date__lt=timed_out)
        )

        pages_in_need_of_review = yield Page.objects.filter(query) \
                                                    .order_by('added_date').find_all()

        if len(pages_in_need_of_review) == 0:
            self.write('')
            self.finish()
            return

        page = choice(pages_in_need_of_review)
        yield page.load_references(['domain', 'last_review'])

        if page.last_review and page.last_review_started_date and page.last_review_started_date < timed_out:
            page.last_review.failure_message = "Timed out after %.0f seconds." % (
                (datetime.now() - page.last_review_started_date).total_seconds()
            )
            yield page.last_review.save()

        review = yield Review.objects.create(
            domain=page.domain,
            page=page,
            facts=[],
            violations=[]
        )

        page.last_review = review
        page.last_review_started_date = datetime.now()
        yield page.save()

        self.write(dumps({
            'page': str(page.uuid),
            'review': str(review.uuid),
            'url': page.url
        }))

        self.finish()
