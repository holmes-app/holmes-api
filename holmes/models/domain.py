#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy import func

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

    def to_dict(self):
        return {
            "url": self.url,
            "name": self.name
        }

    @classmethod
    def get_pages_per_domain(cls, db):
        from holmes.models import Page
        return dict(db.query(Page.domain_id, sa.func.count(Page.id)).group_by(Page.domain_id).all())

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
        from holmes.models import Review, Violation

        result = db.query(sa.func.count(Violation.id).label('count')) \
            .join(Review, Violation.review_id == Review.id) \
            .filter(Review.domain_id == self.id, Review.is_active == True) \
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

    def get_active_reviews(self, db, url_starts_with=None, current_page=1, page_size=10):
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

        if url_starts_with:
            items_query = items_query.filter(Page.url.like('%s%%' % url_starts_with))

        items = items_query.order_by('violations_count desc')[lower_bound:upper_bound]

        return items

    @classmethod
    def get_domain_by_name(self, domain_name, db):
        return db.query(Domain).filter(Domain.name == domain_name).first()

    def get_active_review_count(self, db, url_starts_with=None):
        from holmes.models import Review, Page

        query = db.query(func.count(Review.id)).join(Page, Page.id == Review.page_id).filter(Review.is_active == True, Review.domain_id == self.id)

        if url_starts_with:
            query = query.filter(Page.url.like('%s%%' % url_starts_with))

        return query.scalar()
