#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado import gen
from motorengine import ASCENDING

from holmes.models import Domain, Page
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
                "violationCount": violations_per_domain.get(domain._id, 0),
                "pageCount": pages_per_domain.get(domain._id, 0)
            })

        self.write_json(result)
        self.finish()


class DomainDetailsHandler(BaseHandler):

    @gen.coroutine
    def get(self, domain_name):
        domain = yield Domain.get_domain_by_name(domain_name)
        page_count = yield domain.get_page_count()
        violation_count, violation_points = yield domain.get_violation_data()

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "violationCount": violation_count,
            "violationPoints": violation_points
        }

        self.write_json(domain_json)
        self.finish()


class DomainViolationsPerDayHandler(BaseHandler):

    @gen.coroutine
    def get(self, domain_name):

        domain = yield Domain.get_domain_by_name(domain_name)

        violations_per_day = yield domain.get_violations_per_day()

        domain_json = {
            "name": domain.name,
            "url": domain.url,
            "violations": violations_per_day
        }

        self.write_json(domain_json)
        self.finish()


class DomainReviewsHandler(BaseHandler):

    @gen.coroutine
    def get(self, domain_name):
        current_page = int(self.get_argument('current_page', 1))
        page_size = 10

        domain = yield Domain.get_domain_by_name(domain_name)

        review_count = yield domain.get_active_review_count()
        reviews = yield domain.get_active_reviews(current_page=current_page, page_size=page_size)

        result = {
            'domainName': domain.name,
            'domainURL': domain.url,
            'pageCount': review_count,
            'pages': [],
            'pagesWithoutReview': []
        }

        for review in reviews:
            yield review.page.load_references()

            result['pages'].append({
                "url": review.page.url,
                "uuid": str(review.page.uuid),
                "violationCount": len(review.violations),
                "completedDate": review.completed_date.isoformat(),
                "reviewId": str(review.uuid)
            })

        pages = yield Page.objects.filter(domain=domain, last_review_date__is_null=True).limit(10).find_all()
        for page in pages:
            result['pagesWithoutReview'].append({
                'uuid': str(page.uuid),
                'url': page.url
            })

        page_count = yield Page.objects.filter(domain=domain, last_review_date__is_null=True).count()
        page_count = page_count - len(pages)
        if page_count <= 0:
            page_count = 0

        result['pagesWithoutReviewCount'] = page_count

        self.write_json(result)
        self.finish()
