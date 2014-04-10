#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy import func, distinct

from holmes.models import Base


class Domain(Base):
    __tablename__ = "domains"

    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column('url', sa.String(2000), nullable=False)
    url_hash = sa.Column('url_hash', sa.String(128), nullable=False)
    name = sa.Column('name', sa.String(2000), nullable=False)

    is_active = sa.Column('is_active', sa.Boolean, default=True, nullable=False)

    pages = relationship("Page", backref="domain")
    reviews = relationship("Review", backref="domain")
    violations = relationship("Violation", backref="domain")

    def to_dict(self):
        return {
            "url": self.url,
            "name": self.name
        }

    @classmethod
    def get_pages_per_domain(cls, db):
        from holmes.models import Page
        return dict(db.query(Page.domain_id, sa.func.count(Page.id)).group_by(Page.domain_id).all())

    def get_homepage(self, db):
        from holmes.models import Page

        return db.query(Page).filter(Page.url == self.url).first()

    def get_page_count(self, db):
        from holmes.models import Page
        return db.query(func.count(Page.id)).filter(Page.domain_id == self.id).scalar()

    @classmethod
    def get_violations_per_domain(cls, db):
        from holmes.models import Review, Violation

        violations = db \
            .query(Review.domain_id, sa.func.count(Violation.id).label('count')) \
            .filter(Violation.review_id == Review.id) \
            .filter(Review.is_active == True) \
            .group_by(Review.domain_id) \
            .all()

        domains = {}
        for domain in violations:
            domains[domain.domain_id] = domain.count

        return domains

    def get_violation_data(self, db):
        from holmes.models import Violation

        result = db.query(sa.func.count(Violation.id).label('count')) \
            .filter(
                Violation.domain_id == self.id,
                Violation.review_is_active == True) \
            .one()

        return (
            result.count
        )

    def get_violations_per_day(self, db):
        from holmes.models import Review, Violation  # Prevent circular dependency

        violations = db \
            .query(
                sa.func.year(Review.completed_date).label('year'),
                sa.func.month(Review.completed_date).label('month'),
                sa.func.day(Review.completed_date).label('day'),
                sa.func.count(Violation.id).label('violation_count'),
                sa.func.sum(Violation.points).label('violation_points')
            ).join(
                Domain, Domain.id == Review.domain_id
            ).join(
                Violation, Violation.review_id == Review.id
            ).filter(Review.is_complete == True).filter(Review.domain_id == self.id) \
            .group_by(
                sa.func.year(Review.completed_date),
                sa.func.month(Review.completed_date),
                sa.func.day(Review.completed_date),
            ) \
            .order_by(Review.completed_date) \
            .all()

        result = []

        for day in violations:
            dt = "%d-%d-%d" % (day.year, day.month, day.day)
            result.append({
                "completedAt": dt,
                "violation_count": int(day.violation_count),
                "violation_points": int(day.violation_points)
            })

        return result

    def get_active_reviews(self, db, page_filter=None, current_page=1, page_size=10):
        from holmes.models import Page  # Prevent circular dependency

        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        items_query = db \
            .query(
                Page.url, Page.uuid, Page.last_review_date,
                Page.last_review_uuid, Page.violations_count
            ) \
            .filter(Page.last_review_date != None) \
            .filter(Page.domain == self)

        if page_filter:
            items_query = items_query.filter(Page.url.like('%s/%s%%' % (self.url, page_filter)))

        items = items_query.order_by('violations_count desc')[lower_bound:upper_bound]

        return items

    @classmethod
    def get_domain_by_name(self, domain_name, db):
        return db.query(Domain).filter(Domain.name == domain_name).first()

    def get_active_review_count(self, db, page_filter=None):
        from holmes.models import Review, Page

        query = db.query(func.count(distinct(Review.page_id)))  # See #111

        if page_filter:
            query = query.join(Page, Page.id == Review.page_id) \
                .filter(Page.url.like('%s/%s%%' % (self.url, page_filter)))

        query = query.filter(Review.is_active == True, Review.domain_id == self.id)

        return query.scalar()

    @classmethod
    def get_domain_names(cls, db):
        return [item.name for item in db.query(Domain.name).all()]

    def get_sample_requests(self, db, status_code_filter, limit=20000):
        from holmes.models import Request

        query = db \
            .query(
                Request.id,
                Request.response_time.label('response_time')
            ) \
            .filter(Request.domain_name == self.name)

        query = status_code_filter(query)

        return query \
            .order_by(Request.id.desc()) \
            .limit(limit) \
            .subquery()

    def get_good_request_count(self, db):
        from holmes.models import Request

        sample_query = self.get_sample_requests(
            db,
            lambda query: query.filter(Request.status_code < 400)
        )

        return db \
            .query(func.count(sample_query.columns.id)) \
            .scalar()

    def get_bad_request_count(self, db):
        from holmes.models import Request

        sample_query = self.get_sample_requests(
            db,
            lambda query: query.filter(Request.status_code > 399)
        )

        return db \
            .query(func.count(sample_query.columns.id)) \
            .scalar()

    def get_response_time_avg(self, db):
        from holmes.models import Request

        sample_query = self.get_sample_requests(
            db,
            lambda query: query.filter(Request.status_code < 400)
        )

        time_avg = db \
            .query(func.avg(sample_query.columns.response_time)) \
            .scalar() or 0

        return round(time_avg, 3)

    @classmethod
    def get_domains_details(cls, db):
        domains = db.query(Domain).order_by(Domain.name.asc()).all()

        if not domains:
            return []

        result = []

        for domain in domains:
            page_count = domain.get_page_count(db)
            review_count = domain.get_active_review_count(db)
            violation_count = domain.get_violation_data(db)
            good_request_count = domain.get_good_request_count(db)
            bad_request_count = domain.get_bad_request_count(db)
            response_time_avg = domain.get_response_time_avg(db)

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

        return result

    @classmethod
    def get_active_domains(cls, db):
        return db.query(Domain).filter(Domain.is_active == True).all()
