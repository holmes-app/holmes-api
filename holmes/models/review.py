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

    def add_violation(self, key, value, points):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.violation import Violation  # to avoid circular dependency

        violation = Violation(key=key, value=value, points=int(float(points)))

        self.violations.append(violation)

    @property
    def failed(self):
        return self.failure_message is not None

    @classmethod
    def get_last_reviews(cls, db, limit=12):
        return db.query(Review).filter(Review.is_active == True) \
                               .order_by(Review.completed_date.desc())[:limit]

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
    def get_by_violation_key_name(cls, db, key_id, current_page=1, page_size=10):

        from holmes.models.violation import Violation  # to avoid circular dependency
        from holmes.models.page import Page  # to avoid circular dependency

        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        return db \
            .query(
                Review.uuid.label('review_uuid'),
                Page.url,
                Page.uuid.label('page_uuid'),
                Review.completed_date
            ) \
            .filter(Page.id == Review.page_id) \
            .filter(Violation.review_id == Review.id) \
            .filter(Review.is_active == True) \
            .filter(Violation.key_id == key_id) \
            .order_by(Review.completed_date.desc())[lower_bound:upper_bound]

    @classmethod
    def save_review(cls, page_uuid, review_data, db, fact_definitions, violation_definitions, cache, publish):
        from holmes.models import Page

        page = Page.by_uuid(page_uuid, db)

        page.expires = review_data['expires']

        page.last_modified = review_data['lastModified']

        page.score = 0

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
            review.add_violation(key, violation['value'], violation['points'])

        page.violations_count = len(review_data['violations'])

        review.is_complete = True

        if not page.last_review:
            cache.increment_active_review_count(page.domain)

            cache.increment_violations_count(
                page.domain,
                increment=page.violations_count
            )
        else:
            old_violations_count = len(page.last_review.violations)
            new_violations_count = len(review.violations)

            cache.increment_violations_count(
                page.domain,
                increment=new_violations_count - old_violations_count
            )

            page.last_review.is_active = False

        page.last_review_uuid = review.uuid
        page.last_review = review
        page.last_review_date = review.completed_date

        publish(dumps({
            'type': 'new-review',
            'reviewId': str(review.uuid)
        }))
