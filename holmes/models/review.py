#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

from ujson import dumps
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base


class Review(Base):
    __tablename__ = "reviews"

    id = sa.Column(sa.Integer, primary_key=True)
    is_active = sa.Column('is_active', sa.Boolean, default=False, nullable=False)
    is_complete = sa.Column('is_complete', sa.Boolean, default=False, nullable=False)
    uuid = sa.Column('uuid', sa.String(36), default=uuid4, nullable=False)

    created_date = sa.Column('created_date', sa.DateTime, default=datetime.utcnow, nullable=False)
    completed_date = sa.Column('completed_date', sa.DateTime, nullable=True)
    completed_day = sa.Column('completed_day', sa.Date, nullable=True)

    failure_message = sa.Column('failure_message', sa.String(2000), nullable=True)

    domain_id = sa.Column('domain_id', sa.Integer, sa.ForeignKey('domains.id'))
    page_id = sa.Column('page_id', sa.Integer, sa.ForeignKey('pages.id'))

    facts = relationship("Fact", cascade="all,delete")
    violations = relationship("Violation", cascade="all,delete")

    def to_dict(self, fact_definitions, violation_definitions):
        return {
            'page': self.page and self.page.to_dict() or None,
            'domain': self.domain and self.domain.name or None,
            'isComplete': self.is_complete,
            'uuid': str(self.uuid),
            'createdAt': self.created_date,
            'completedAt': self.completed_date,
            'facts': [fact.to_dict(fact_definitions) for fact in self.facts],
            'violations': [violation.to_dict(violation_definitions) for violation in self.violations]
        }

    def __str__(self):
        return str(self.uuid)

    def __repr__(self):
        return str(self)

    def add_fact(self, key, value):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.fact import Fact  # to avoid circular dependency

        fact = Fact(key=key, value=value)

        self.facts.append(fact)

    def add_violation(self, key, value, points, domain):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.violation import Violation  # to avoid circular dependency

        violation = Violation(
            key=key,
            value=value,
            points=int(float(points)),
            domain=domain
        )

        self.violations.append(violation)

    @property
    def failed(self):
        return self.failure_message is not None

    @classmethod
    def get_last_reviews(cls, db, domain_filter=None, limit=12):
        query = db.query(Review).filter(Review.is_active == True)

        if domain_filter:
            from holmes.models.domain import Domain
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                query = query.filter(Review.domain_id == domain.id)

        return query.order_by(Review.completed_date.desc())[:limit]

    @classmethod
    def get_reviews_count_in_period(cls, db, from_date, domain_filter=None,
                                    to_date=None):
        if to_date is None:
            to_date = datetime.utcnow()

        reviews = db \
            .query(Review.completed_date) \
            .filter(Review.is_active == True) \
            .filter(Review.completed_date.between(from_date, to_date))

        if domain_filter:
            from holmes.models.domain import Domain
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                reviews = reviews.filter(Review.domain_id == domain.id)

        reviews = reviews.order_by(Review.completed_date.asc()).all()

        count = len(reviews)

        first_date = None
        if count > 0:
            first_date = reviews[0].completed_date

        return count, first_date

    def get_violation_points(self):
        points = 0
        for violation in self.violations:
            points += violation.points
        return points

    @classmethod
    def by_uuid(cls, uuid, db):
        return db.query(Review).filter(Review.uuid == uuid).first()

    @property
    def violation_count(self):
        return len(self.violations)

    @classmethod
    def count_by_violation_key_name(cls, db, key_id, domain_filter=None, page_filter=None):
        from holmes.models.review import Review  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency

        query = db \
            .query(sa.func.count(Violation.id)) \
            .filter(Violation.review_is_active == 1) \
            .filter(Violation.key_id == key_id)

        if domain_filter:
            from holmes.models.domain import Domain  # to avoid circular dependency
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                query = query.filter(Violation.domain_id == domain.id)

                if page_filter:
                    from holmes.models.page import Page  # to avoid circular dependency
                    query = query.filter(Review.id == Violation.review_id) \
                        .filter(Page.id == Review.page_id) \
                        .filter(
                            Page.url.like(
                                '{0}/{1}%'.format(domain.url, page_filter)
                            )
                        )

        # FIXME: Maybe group by review? Considering there should be only one
        # Violation of a given Key for every Review -- weither active or not
        # See test/unit/models/test_review.py:216 (also see #111)
        return query.scalar()

    @classmethod
    def get_by_violation_key_name(cls, db, key_id, current_page=1, page_size=10, domain_filter=None, page_filter=None):
        from holmes.models.page import Page  # to avoid circular dependency
        from holmes.models.review import Review  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency
        from holmes.models.domain import Domain  # to avoid circular dependency

        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        query = db \
            .query(
                Review.uuid.label('review_uuid'),
                Page.url,
                Page.uuid.label('page_uuid'),
                Review.completed_date,
                Domain.name.label('domain_name')
            ) \
            .filter(Violation.key_id == key_id) \
            .filter(Review.id == Violation.review_id) \
            .filter(Review.is_active == 1) \
            .filter(Page.id == Review.page_id) \
            .filter(Domain.id == Review.domain_id)

        if domain_filter:
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                query = query.filter(Review.domain_id == domain.id)

                if page_filter:
                    query = query.filter(
                        Page.url.like(
                            u'{0}/{1}%'.format(domain.url, page_filter)
                        )
                    )

        # FIXME: Maybe group by review? Considering there should be only one
        # Violation of a given Key for every Review -- weither active or not
        # See test/unit/models/test_review.py:242 (also see #111)
        return query.order_by(Review.completed_date.desc())[lower_bound:upper_bound]

    @classmethod
    def save_review(cls, page_uuid, review_data, db, fact_definitions, violation_definitions, cache, publish, config):
        from holmes.models import Page

        page = Page.by_uuid(page_uuid, db)
        last_review = page.last_review

        review = Review(
            domain_id=page.domain.id,
            page_id=page.id,
            is_active=True,
            is_complete=False,
            completed_date=datetime.utcnow(),
            uuid=uuid4(),
        )

        db.add(review)

        for fact in review_data['facts']:
            name = fact['key']
            key = fact_definitions[name]['key']
            review.add_fact(key, fact['value'])

        for violation in review_data['violations']:
            name = violation['key']
            key = violation_definitions[name]['key']
            review.add_violation(
                key,
                violation['value'],
                violation['points'],
                page.domain
            )

        page.expires = review_data['expires']
        page.last_modified = review_data['lastModified']
        page.last_review_uuid = review.uuid
        page.last_review = review
        page.last_review_date = review.completed_date
        page.violations_count = len(review_data['violations'])

        review.is_complete = True

        if not last_review:
            cache.increment_active_review_count(page.domain)
        else:
            for violation in last_review.violations:
                violation.review_is_active = False

            last_review.is_active = False

        Review.delete_old_reviews(db, config, page)

        publish(dumps({
            'type': 'new-review',
            'reviewId': str(review.uuid)
        }))

    @classmethod
    def delete_old_reviews(cls, db, config, page):
        reviews = db \
            .query(Review) \
            .filter(Review.is_active == 0) \
            .filter(Review.page_id == page.id) \
            .order_by(Review.completed_date.desc()) \
            .all()

        last_reviews = reviews[config.NUMBER_OF_REVIEWS_TO_KEEP:]

        if len(last_reviews) > 0:
            for review in last_reviews:
                db.delete(review)
