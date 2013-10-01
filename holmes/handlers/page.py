#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID

from tornado.web import RequestHandler
from tornado import gen
from ujson import dumps

from holmes.models import Page, Domain
from holmes.utils import get_domain_from_url


class PageHandler(RequestHandler):

    @gen.coroutine
    def post(self):
        url = self.get_argument('url')

        domain_name, domain_url = get_domain_from_url(url)
        if not domain_name:
            self.set_status(400, "Invalid url [%s]" % url)
            self.finish()
            return

        domain = yield Domain.objects.get(url=domain_url)

        if not domain:
            domain = yield Domain.objects.create(url=domain_url, name=domain_name)

        page = yield Page.objects.get(url=url)

        if page:
            self.set_status(409, "Duplicate entry for page [%s]" % url)
            self.finish()
            return

        page = yield Page.objects.create(url=url, domain=domain)

        self.write(str(page.uuid))
        self.finish()

    @gen.coroutine
    def get(self, uuid=""):
        uuid = UUID(uuid)

        page = yield Page.objects.get(uuid=uuid)

        if not page:
            self.set_status(404, "Page UUID [%s] not found" % uuid)
            self.finish()
            return
    
        page_json = {
            "uuid": str(page.uuid),
            "title": page.title,
            "url": page.url
        }

        self.write(page_json)  # dumps(page)
        self.finish()
