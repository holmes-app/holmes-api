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
            review_count = yield self.cache.get_review_count(domain)
            violation_count = yield self.cache.get_violation_count(domain)

            result.append({
                "url": domain.url,
                "name": domain.name,
                "violationCount": violation_count,
                "pageCount": page_count,
                "reviewCount": review_count,
                "reviewPercentage": round(float(review_count) / page_count * 100, 2)
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
        review_count = yield self.cache.get_review_count(domain)
        violation_count = yield self.cache.get_violation_count(domain)

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "reviewCount": review_count,
            "violationCount": violation_count,
            "reviewPercentage": round(float(review_count) / page_count * 100, 2)
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

    def get(self, domain_name):
        current_page = int(self.get_argument('current_page', 1))
        page_size = 10

        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        reviews = domain.get_active_reviews(self.db, current_page=current_page, page_size=page_size)

        result = {
            'domainName': domain.name,
            'domainURL': domain.url,
            'pages': [],
        }

        for review in reviews:
            result['pages'].append({
                "url": review.page.url,
                "uuid": str(review.page.uuid),
                "violationCount": len(review.violations),
                "completedAt": review.completed_date,
                "reviewId": str(review.uuid)
            })

        self.write_json(result)
