#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID
from ujson import loads

from tornado import gen
from motorengine import Q
import logging

from holmes.models import Page, Domain
from holmes.utils import get_domain_from_url
from holmes.handlers import BaseHandler


class PageHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        post_data = loads(self.request.body)

        url = post_data['url']

        domain_name, domain_url = get_domain_from_url(url)
        if not domain_name:
            self.set_status(400, 'Invalid url [%s]' % url)
            self.finish()
            return

        query = (
            Q(name=domain_name) |
            Q(name=domain_name.rstrip('/')) |
            Q(name="%s/" % domain_name)
        )

        domains = yield Domain.objects.filter(query).find_all()

        if not domains:
            domain = None
        else:
            domain = domains[0]

        if not domain:
            domain = yield Domain.objects.create(url=domain_url, name=domain_name)

        query = (
            Q(url=url) |
            Q(url=url.rstrip('/')) |
            Q(url="%s/" % url)
        )

        pages = yield Page.objects.filter(query).find_all()

        if pages:
            page = pages[0]
        else:
            page = None

        if page:
            self.write(str(page.uuid))
            self.finish()
            return

        page = yield Page.objects.create(url=url, domain=domain)

        self.write(str(page.uuid))
        self.finish()

    def options(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT')
        self.set_header('Access-Control-Allow-Headers', 'Accept, Content-Type')
        self.set_status(200)
        self.finish()

    @gen.coroutine
    def get(self, uuid=''):
        uuid = UUID(uuid)

        page = yield Page.objects.get(uuid=uuid)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            self.finish()
            return

        page_json = {
            "uuid": str(page.uuid),
            "title": page.title,
            "url": page.url
        }

        self.write(page_json)  # dumps(page)
        self.finish()


class PagesHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        urls = self.get_arguments('url')

        if not urls:
            self.set_status(200)
            self.write('0')
            self.finish()
            return

        pages_to_add = []

        all_domains = []
        for url in urls:
            domain_name, domain_url = get_domain_from_url(url)
            if not domain_name:
                self.set_status(400, 'In the urls you posted there is an invalid URL: %s' % url)
                self.finish()
                return
            all_domains.append((domain_name, domain_url))

        existing_domains = yield Domain.objects.filter(name__in=[domain[0] for domain in all_domains]).find_all()
        existing_domains_dict = dict([(domain.name, domain) for domain in existing_domains])

        domains_to_add = [
            Domain(name=domain[0], url=domain[1])
            for domain in all_domains
            if not domain[0] in existing_domains_dict
        ]
        domains_to_add_dict = dict([(domain.name, domain) for domain in domains_to_add])

        all_domains_dict = {}
        all_domains_dict.update(existing_domains_dict)
        all_domains_dict.update(domains_to_add_dict)

        existing_pages = yield Page.objects.filter(url__in=urls).find_all()
        if not existing_pages:
            existing_pages = []
        existing_pages_dict = dict([(page.url, page) for page in existing_pages])

        pages_to_add = []

        for url in urls:
            if url in existing_pages_dict:
                continue
            domain_name, domain_url = get_domain_from_url(url.strip())
            domain = all_domains_dict[domain_name]

            logging.debug("Adding URL: %s" % url)
            pages_to_add.append(Page(url=url, domain=domain))

        if domains_to_add:
            yield Domain.objects.bulk_insert(domains_to_add)

        if pages_to_add:
            yield Page.objects.bulk_insert(pages_to_add)

        self.write(str(len(pages_to_add)))
        self.finish()

    def options(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.write('OK')
        self.finish()
