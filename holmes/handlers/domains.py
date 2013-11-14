#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen

from holmes.models import Domain, Page
from holmes.handlers import BaseHandler


class DomainsHandler(BaseHandler):

    @gen.coroutine
    def get(self):
        domains = self.db.query(Domain).order_by(Domain.name.asc()).all()
        violations_per_domain = Domain.get_violations_per_domain(self.db)
        pages_per_domain = Domain.get_pages_per_domain(self.db)

        if not domains:
            self.write("[]")
            self.finish()
            return

        result = []

        for domain in domains:
            result.append({
                "url": domain.url,
                "name": domain.name,
                "violationCount": violations_per_domain.get(domain.id, 0),
                "pageCount": pages_per_domain.get(domain.id, 0)
            })

        self.write_json(result)
        self.finish()


class DomainDetailsHandler(BaseHandler):

    @gen.coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            self.finish()
            return

        page_count = domain.get_page_count(self.db)
        violation_count, violation_points = domain.get_violation_data(self.db)

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "violationCount": violation_count,
            "violationPoints": violation_points or 0
        }

        self.write_json(domain_json)
        self.finish()


class DomainViolationsPerDayHandler(BaseHandler):

    @gen.coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            self.finish()
            return

        violations_per_day = domain.get_violations_per_day(self.db)

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "violations": violations_per_day
        }

        self.write_json(domain_json)
        self.finish()


class DomainReviewsHandler(BaseHandler):

    def get(self, domain_name):
        current_page = int(self.get_argument('current_page', 1))
        page_size = 10

        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            self.finish()
            return

        review_count = domain.get_active_review_count(self.db)
        reviews = domain.get_active_reviews(self.db, current_page=current_page, page_size=page_size)

        result = {
            'domainName': domain.name,
            'domainURL': domain.url,
            'pageCount': review_count,
            'pages': [],
            'pagesWithoutReview': []
        }

        for review in reviews:
            result['pages'].append({
                "url": review.page.url,
                "uuid": str(review.page.uuid),
                "violationCount": len(review.violations),
                "completedDate": review.completed_date.isoformat(),
                "reviewId": str(review.uuid)
            })

        pages = self.db.query(Page).filter(Page.domain == domain, Page.last_review_date == None)[:10]
        for page in pages:
            result['pagesWithoutReview'].append({
                'uuid': str(page.uuid),
                'url': page.url
            })

        page_count = self.db.query(Page).filter(Page.domain == domain, Page.last_review_date == None).count()
        page_count = page_count - len(pages)
        if page_count <= 0:
            page_count = 0

        result['pagesWithoutReviewCount'] = page_count

        self.write_json(result)
