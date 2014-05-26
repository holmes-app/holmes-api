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
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        result = self.girl.get('domains_details')
        data = next((l for l in result if l['name'] == domain_name), None)

        if not data:
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        page_count = data.get('pageCount', 0)
        review_count = data.get('reviewCount', 0)
        violation_count = data.get('violationCount', 0)
        error_percentage = data.get('errorPercentage', 0)
        response_time_avg = data.get('averageResponseTime', 0)
        review_percentage = data.get('reviewPercentage', 0)

        domain_json = {
            "id": domain.id,
            "name": domain.name,
            "url": domain.url,
            "pageCount": page_count,
            "reviewCount": review_count,
            "violationCount": violation_count,
            "reviewPercentage": review_percentage,
            "is_active": domain.is_active,
            "errorPercentage": error_percentage,
            "averageResponseTime": response_time_avg,
            "homepageId": "",
            "homepageReviewId": "",
        }

        homepage = domain.get_homepage(self.db)

        if homepage:
            if homepage.uuid:
                domain_json["homepageId"] = str(homepage.uuid)
            if homepage.last_review_uuid:
                domain_json["homepageReviewId"] = str(homepage.last_review_uuid)

        self.write_json(domain_json)


class DomainViolationsPerDayHandler(BaseHandler):

    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, self._('Domain %s not found') % domain_name)
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
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        reviews = yield self.application.search_provider.get_domain_active_reviews(
            domain=domain,
            current_page=current_page,
            page_size=page_size,
            page_filter=term,
        )

        if 'reviewsCount' not in reviews:
            if not term:
                reviews['reviewsCount'] = yield self.cache.get_active_review_count(domain)
            else:
                reviews['reviewsCount'] = None

        self.write_json(reviews)
        self.finish()


class DomainGroupedViolationsHandler(BaseHandler):

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        violation_defs = self.application.violation_definitions

        grouped_violations = self.girl.get('violation_count_by_category_for_domains')

        total = 0
        violations = []

        for item in grouped_violations.get(domain.id, []):
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
            self.set_status(404, self._('Domain %s not found') % domain_name)
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
                'count': count,
                'key': key_name,
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
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        domain.is_active = not domain.is_active

        if not domain.is_active:
            yield self.cache.delete_limit_usage_by_domain(domain.url)

    @coroutine
    def options(self, domain_name):
        super(DomainsChangeStatusHandler, self).options()
