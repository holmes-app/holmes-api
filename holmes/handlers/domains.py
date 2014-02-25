#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.gen import coroutine

from holmes.models import Domain, Request
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
            good_request_count = yield self.cache.get_good_request_count(domain)
            bad_request_count = yield self.cache.get_bad_request_count(domain)
            response_time_avg = yield self.cache.get_response_time_avg(domain)

            if page_count > 0:
                review_percentage = round(float(review_count) / page_count * 100, 2)
            else:
                review_percentage = 0

            total_request_count = good_request_count + bad_request_count
            if total_request_count > 0:
                error_percentage = round(float(bad_request_count) / total_request_count * 100, 2)
            else:
                error_percentage = 0

            result.append({
                "id": domain.id,
                "url": domain.url,
                "name": domain.name,
                "violationCount": violation_count,
                "pageCount": page_count,
                "reviewCount": review_count,
                "reviewPercentage": review_percentage,
                "errorPercentage": error_percentage,
                "is_active": domain.is_active,
                "averageResponseTime": response_time_avg,
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

        bad_request_count = yield self.cache.get_bad_request_count(domain)
        good_request_count = yield self.cache.get_good_request_count(domain)
        total_request_count = good_request_count + bad_request_count
        if total_request_count > 0:
            error_percentage = round(float(bad_request_count) / total_request_count * 100, 2)
        else:
            error_percentage = 0

        response_time_avg = yield self.cache.get_response_time_avg(domain)

        status_code_info = Request.get_status_code_info(domain_name, self.db)

        if page_count > 0:
            review_percentage = round(float(review_count) / page_count * 100, 2)
        else:
            review_percentage = 0

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "reviewCount": review_count,
            "violationCount": violation_count,
            "reviewPercentage": review_percentage,
            "is_active": domain.is_active,
            "statusCodeInfo": status_code_info,
            "errorPercentage": error_percentage,
            "averageResponseTime": response_time_avg,
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
            "id": domain.id,
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
        page_size = int(self.get_argument('page_size', 10))

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
            "domainId": domain.id,
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

    @coroutine
    def options(self, domain_name):
        super(DomainsChangeStatusHandler, self).options()
