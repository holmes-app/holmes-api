#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import dumps

from tornado import gen
from motorengine import ASCENDING

from holmes.models import Domain
from holmes.handlers import BaseHandler


class DomainsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        queryset = Domain.objects.order_by(Domain.name, ASCENDING)

        domains = yield queryset.find_all()

        if not domains:
            self.write("[]")
            self.finish()
            return

        self.write(dumps([domain.to_dict() for domain in domains]))
        self.finish()
