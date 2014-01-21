#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.gen import coroutine

from holmes.models import Domain
from holmes.handlers import BaseHandler


class DomainsHandler(BaseHandler):

    @coroutine
    def get(self):
        domains = self.db.query(Domain).order_by(Domain.name.asc()).all()

        if not domains:
            self.write("[]")
            return

        result = []

        for domain in domains:
            page_count = yield self.cache.get_page_count(domain)
            review_count = yield self.cache.get_active_review_count(domain)
            violation_count = yield self.cache.get_violation_count(domain)

            if page_count > 0:
                review_percentage = round(float(review_count) / page_count * 100, 2)
            else:
                review_percentage = 0

            result.append({
                "url": domain.url,
                "name": domain.name,
                "violationCount": violation_count,
                "pageCount": page_count,
                "reviewCount": review_count,
                "reviewPercentage": review_percentage,
                "is_active": domain.is_active,
            })

        self.write_json(result)


class DomainDetailsHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        page_count = yield self.cache.get_page_count(domain)
        review_count = yield self.cache.get_active_review_count(domain)
        violation_count = yield self.cache.get_violation_count(domain)

        if page_count > 0:
            review_percentage = round(float(review_count) / page_count * 100, 2)
        else:
            review_percentage = 0

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "reviewCount": review_count,
            "violationCount": violation_count,
            "reviewPercentage": review_percentage,
            "is_active": domain.is_active,
        }

        self.write_json(domain_json)


class DomainViolationsPerDayHandler(BaseHandler):

    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        violations_per_day = domain.get_violations_per_day(self.db)

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "violations": violations_per_day
        }

        self.write_json(domain_json)


class DomainReviewsHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        term = self.get_argument('term', None)
        current_page = int(self.get_argument('current_page', 1))
        page_size = 10

        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        reviews = domain.get_active_reviews(
            self.db,
            url_starts_with=term,
            current_page=current_page,
            page_size=page_size
        )

        page_count = yield self.cache.get_page_count(domain)
        if term:
            review_count = domain.get_active_review_count(url_starts_with=term, db=self.db)
        else:
            review_count = yield self.cache.get_active_review_count(domain)

        result = {
            'domainName': domain.name,
            'domainURL': domain.url,
            'reviewCount': review_count,
            'pageCount': page_count,
            'pages': [],
        }

        for page in reviews:
            result['pages'].append({
                "url": page.url,
                "uuid": str(page.uuid),
                "violationCount": page.violations_count,
                "completedAt": page.last_review_date,
                "reviewId": str(page.last_review_uuid)
            })

        self.write_json(result)


class DomainsChangeStatusHandler(BaseHandler):

    @coroutine
    def post(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        domain.is_active = not domain.is_active
