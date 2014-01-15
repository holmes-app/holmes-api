#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import UUID
import hashlib

from ujson import loads, dumps
from tornado import gen
import tornado.httpclient
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
        score = float(post_data.get('score', self.application.config.DEFAULT_PAGE_SCORE))

        domain_name, domain_url = get_domain_from_url(url)
        if not domain_name:
            self.set_status(400, 'Invalid url [%s]' % url)
            self.write_json({
                'reason': 'invalid_url',
                'url': url
            })
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
            return

        if response.effective_url != url:
            self.set_status(400, 'Redirect URL [%s]' % url)
            self.write_json({
                'reason': 'redirect',
                'url': url,
                'effectiveUrl': response.effective_url
            })
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

            self.application.event_bus.publish(dumps({
                'type': 'new-domain',
                'domainUrl': str(domain_url)
            }))

        pages = self.db.query(Page).filter(or_(
            Page.url == url,
            Page.url == url.rstrip('/'),
            Page.url == "%s/" % url
        )).all()

        if pages:
            page = pages[0]
            page.score += score  # if page exists we need to increase page score
        else:
            page = None

        if page:
            self.write(str(page.uuid))
            return

        url_hash = hashlib.sha512(url).hexdigest()

        page = Page(url=url, url_hash=url_hash, domain=domain, score=score)
        self.db.add(page)
        self.db.flush()

        yield self.cache.increment_page_count(domain)
        yield self.cache.increment_page_count()

        self.application.event_bus.publish(dumps({
            'type': 'new-page',
            'pageUrl': str(url)
        }))

        self.write(str(page.uuid))

    def get(self, uuid=''):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        page_json = {
            "uuid": str(page.uuid),
            "url": page.url
        }

        self.write(page_json)


class PageReviewsHandler(BaseHandler):

    def get(self, uuid='', limit=10):
        uuid = UUID(uuid)

        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        reviews = self.db.query(Review) \
            .filter(Review.page == page) \
            .filter(Review.is_complete == True) \
            .order_by(Review.completed_date.desc())[:limit]

        result = []
        for review in reviews:
            result.append({
                'uuid': str(review.uuid),
                'completedAt': review.completed_date,
                'violationCount': review.violation_count
            })

        self.write_json(result)


class PagesHandler(BaseHandler):

    @gen.coroutine
    def post(self):
        urls = self.get_arguments('url')

        if not urls:
            self.set_status(200)
            self.write('0')
            return

        all_domains = []
        for url in urls:
            domain_name, domain_url = get_domain_from_url(url.strip())
            if not domain_name:
                self.set_status(400, 'In the urls you posted there is an invalid URL: %s' % url)
                return
            all_domains.append((domain_name, domain_url))

        domains = self.add_domains(all_domains)

        existing_pages = self.db.query(Page).filter(Page.url.in_(urls)).all()
        if not existing_pages:
            existing_pages = []
        existing_pages_dict = dict([(page.url, page) for page in existing_pages])

        added_pages = []
        for url in set(urls):
            if url in existing_pages_dict:
                continue

            page_url = str(url)

            url_hash = hashlib.sha512(page_url).hexdigest()

            has_lock = yield self.cache.has_lock(url_hash)
            if has_lock:
                logging.debug('Lock found in page %s. Skipping...' % page_url)
                continue

            yield self.cache.lock_page(url_hash)

            domain_name, domain_url = get_domain_from_url(url.strip())

            logging.debug("Adding URL: %s" % url)

            domain = domains[domain_url]
            page = Page(url=page_url, url_hash=url_hash, domain=domain)
            self.db.add(page)
            self.db.flush()

            yield self.cache.increment_page_count(domain)
            added_pages.append(page)

        if added_pages:
            self.application.event_bus.publish(dumps({
                'type': 'new-page',
                'pageUrl': added_pages[0].url
            }))

        pages = list(added_pages)

        self.write(str(len(pages)))

    def add_domains(self, domains):
        resulting_domains = {}

        #existing_domains = self.db.query(Domain.id, Domain.url).filter(
            #or_(
                #Domain.url.in_([
                    #domain[1] for domain in domains
                #]),
                #Domain.url.in_([
                    #domain[1].rstrip('/') for domain in domains
                #]),
                #Domain.url.in_([
                    #"%s/" % domain[1] for domain in domains
                #])
            #)
        #).all()
        #existing_domain_dict = dict([(domain[0], domain[1]) for domain in existing_domains])

        for domain_name, domain_url in domains:
            if domain_url in resulting_domains:
                continue

            domain = self.db.query(Domain).filter(or_(
                Domain.url == domain_url,
                Domain.url == domain_url.rstrip('/')
            )).first()

            if domain:
                resulting_domains[domain_url] = domain
                continue

            key = domain_url.rstrip('/')
            domain = self.db.query(Domain).filter(Domain.url == key).first()
            if domain:
                resulting_domains[domain_url] = domain
                continue

            key = ("%s/" % domain_url)
            domain = self.db.query(Domain).filter(Domain.url == key).first()
            if domain:
                resulting_domains[domain_url] = domain
                continue

            resulting_domains[domain_url] = Domain(
                name=domain_name,
                url=domain_url,
                url_hash=hashlib.sha512(domain_url).hexdigest())

            self.db.add(resulting_domains[domain_url])

            self.application.event_bus.publish(dumps({
                'type': 'new-domain',
                'domainUrl': domain_url
            }))

        self.db.flush()
        return resulting_domains


class PageViolationsPerDayHandler(BaseHandler):

    def get(self, uuid):
        page = Page.by_uuid(uuid, self.db)

        if not page:
            self.set_status(404, 'Page UUID [%s] not found' % uuid)
            return

        violations_per_day = page.get_violations_per_day(self.db)

        page_json = {
            "violations": violations_per_day
        }

        self.write_json(page_json)
