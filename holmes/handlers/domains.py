#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen
from motorengine import ASCENDING

from holmes.models import Domain
from holmes.handlers import BaseHandler


class DomainsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        domains = yield Domain.objects.order_by(Domain.name, ASCENDING).find_all()
        violations_per_domain = yield Domain.get_violations_per_domain()
        pages_per_domain = yield Domain.get_pages_per_domain()

        if not domains:
            self.write("[]")
            self.finish()
            return

        result = []

        for domain in domains:
            result.append({
                "url": domain.url,
                "name": domain.name,
                "violationCount": violations_per_domain.get(domain.name, 0),
                "pageCount": pages_per_domain.get(domain.name, 0)
            })

        self.write_json(result)
        self.finish()
