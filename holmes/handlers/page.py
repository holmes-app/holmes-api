#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID
import hashlib

from ujson import loads
from tornado import gen
import tornado.httpclient
#from motorengine import Q, DESCENDING
import logging
from sqlalchemy import or_

from holmes.models import Page, Domain, Review
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
            self.write_json({
                'reason': 'invalid_url',
                'url': url
            })
            self.finish()
            return

        phost = self.application.config.HTTP_PROXY_HOST
        pport = self.application.config.HTTP_PROXY_PORT

        request = tornado.httpclient.HTTPRequest(
            url=url,
            proxy_host=phost,
            proxy_port=pport
        )

        logging.info('Obtaining "%s" using proxy "%s:%s"...' % (url, phost, pport))

        response = yield tornado.gen.Task(self.application.http_client.fetch, request)
        if response.code > 399:
            self.set_status(400, 'Invalid URL [%s]' % url)
            self.write_json({
                'reason': 'invalid_url',
                'url': url
            })
            self.finish()
            return

        if response.effective_url != url:
            self.set_status(400, 'Redirect URL [%s]' % url)
            self.write_json({
                'reason': 'redirect',
                'url': url,
                'effectiveUrl': response.effective_url
            })
            self.finish()
            return

        domains = self.db.query(Domain).filter(or_(
            Domain.name == domain_name,
            Domain.name == domain_name.rstrip('/'),
            Domain.name == "%s/" % domain_name
        )).all()

        if not domains:
            domain = None
        else:
            domain = domains[0]

        if not domain:
            url_hash = hashlib.sha512(domain_url).hexdigest()
            domain = Domain(url=domain_url, url_hash=url_hash, name=domain_name)
            self.db.add(domain)
            self.db.flush()

        pages = self.db.query(Page).filter(or_(
            Page.url == url,
            Page.url == url.rstrip('/'),
            Page.url == "%s/" % url
        )).all()

        if pages:
            page = pages[0]
        else:
            page = None

        if page:
            self.write(str(page.uuid))
            self.finish()
            return

        url_hash = hashlib.sha512(url).hexdigest()

        page = Page(url=url, url_hash=url_hash, domain=domain)
        self.db.add(page)
        self.db.flush()

        self.write(str(page.uuid))
        self.finish()

    @gen.coroutine
    def get(self, uuid=''):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            self.finish()
            return

        page_json = {
            "uuid": str(page.uuid),
            "url": page.url
        }

        self.write(page_json)
        self.finish()


class PageReviewsHandler(BaseHandler):

    @gen.coroutine
    def get(self, uuid='', limit=10):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            self.finish()
            return

        reviews = self.db.query(Review) \
            .filter(Review.page == page) \
            .filter(Review.is_complete == True) \
            .order_by(Review.completed_date.desc())[:limit]

        result = []
        for review in reviews:
            result.append({
                'uuid': str(review.uuid),
                'completedDate': review.completed_date.isoformat(),
                'violationCount': review.violation_count
            })

        self.write_json(result)
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

        existing_domains = self.db.query(Domain).filter(Domain.name.in_([domain[0] for domain in all_domains])).all()
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

        existing_pages = self.db.query(Page).filter(Page.url.in_(urls)).all()
        if not existing_pages:
            existing_pages = []
        existing_pages_dict = dict([(page.url, page) for page in existing_pages])

        pages_to_add = []
        for url in set(urls):
            if url in existing_pages_dict:
                continue
            domain_name, domain_url = get_domain_from_url(url.strip())
            domain = all_domains_dict[domain_name]

            logging.debug("Adding URL: %s" % url)
            url_hash = hashlib.sha512(url).hexdigest()
            pages_to_add.append(Page(url=url, url_hash=url_hash, domain=domain))

        if domains_to_add:
            for domain in domains_to_add:
                self.db.add(domain)

        if pages_to_add:
            for page in pages_to_add:
                self.db.add(page)

        self.write(str(len(pages_to_add)))
        self.finish()


class PageViolationsPerDayHandler(BaseHandler):

    def get(self, uuid):
        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            self.finish()
            return

        violations_per_day = page.get_violations_per_day(self.db)

        page_json = {
            "violations": violations_per_day
        }

        self.write_json(page_json)
        self.finish()
