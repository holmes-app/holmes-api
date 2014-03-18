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
            result.append({
                "id": domain.id,
                "url": domain.url,
                "name": domain.name,
                "is_active": domain.is_active
            })

        self.write_json(result)


class DomainsFullDataHandler(BaseHandler):

    @coroutine
    def get(self):
        result = self.girl.get('domains_details')
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


class DomainPageCountHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        page_count = yield self.cache.get_page_count(domain)

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "is_active": domain.is_active,
            "pageCount": page_count
        }

        self.write_json(domain_json)


class DomainReviewCountHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        review_count = yield self.cache.get_active_review_count(domain)

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "is_active": domain.is_active,
            "reviewCount": review_count
        }

        self.write_json(domain_json)


class DomainViolationCountHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        violation_count = yield self.cache.get_violation_count(domain)

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "is_active": domain.is_active,
            "violationCount": violation_count
        }

        self.write_json(domain_json)


class DomainErrorPercentageHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        bad_request_count = yield self.cache.get_bad_request_count(domain)
        good_request_count = yield self.cache.get_good_request_count(domain)
        total_request_count = good_request_count + bad_request_count
        if total_request_count > 0:
            error_percentage = round(float(bad_request_count) / total_request_count * 100, 2)
        else:
            error_percentage = 0

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "is_active": domain.is_active,
            "errorPercentage": error_percentage
        }

        self.write_json(domain_json)


class DomainResponseTimeAvgHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        response_time_avg = yield self.cache.get_response_time_avg(domain)

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "is_active": domain.is_active,
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


class DomainGroupedViolationsHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        violation_defs = self.application.violation_definitions

        grouped_violations = self.girl.get('violation_count_by_category_for_domains')

        total = 0
        violations = []

        for item in grouped_violations.get(domain.id, None):
            key_name, key_category_id, count = item['key_name'], item['category_id'], item['violation_count']
            violations.append({
                'categoryId': key_category_id,
                'categoryName': violation_defs[key_name]['category'],
                'count': count
            })
            total += count

        result = {
            "domainId": domain.id,
            'domainName': domain.name,
            'domainURL': domain.url,
            'total': total,
            'violations': violations
        }

        self.write_json(result)


class DomainTopCategoryViolationsHandler(BaseHandler):

    @coroutine
    def get(self, domain_name, key_category_id):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, 'Domain %s not found' % domain_name)
            return

        violation_defs = self.application.violation_definitions

        top_violations = yield self.cache.get_top_in_category_for_domain(
            domain,
            key_category_id,
            self.application.config.get('TOP_CATEGORY_VIOLATIONS_LIMIT')
        )

        violations = []
        for key_name, count in top_violations:
            violations.append({
                'title': violation_defs[key_name]['title'],
                'count': count
            })

        result = {
            "domainId": domain.id,
            'domainName': domain.name,
            'domainURL': domain.url,
            'categoryId': key_category_id,
            'violations': violations
        }

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
