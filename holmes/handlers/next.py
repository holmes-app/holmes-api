#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen
from datetime import datetime, timedelta
from ujson import dumps

from holmes.models.page import Page
from holmes.models.review import Review


class NextHandler(RequestHandler):

    @gen.coroutine
    def get(self):
        yesterday = datetime.now() - timedelta(1)

        next_pages = yield Page.objects.filter(added_date__lt=yesterday).find_all()

        if not next_pages:
            self.write(dumps(None))
            self.finish()
            return

        next_page = next_pages[0]

        review = yield Review.objects.create(page=next_page)

        next_page.updated_date = datetime.now()
        yield next_page.save()

        yield review.load_references(['page'])
        self.write(dumps(review.to_dict()))
        self.finish()
