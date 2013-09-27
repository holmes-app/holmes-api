#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.web import RequestHandler
from tornado import gen

from holmes.models import Page, Domain
from holmes.utils import get_domain_from_url


class PageHandler(RequestHandler):

    @gen.coroutine
    def post(self):
        url = self.get_argument('url')

        domain_url = get_domain_from_url(url)
        if not domain_url:
            self.set_status(400, "Invalid url [%s]" % url)
            self.finish()
            return

        domain = yield Domain.objects.filter(url=domain_url).find_all()

        if not domain:
            domain = yield Domain.objects.create(url=domain_url)
            page = yield Page.objects.create(url=url)

        self.write(page._id)
        self.finish()

    def get(self):
        pass