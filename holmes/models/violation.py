#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from collections import defaultdict

from holmes.models import Base, JsonTypeGzipped
from holmes.models.keys import Key


class Violation(Base):
    __tablename__ = "violations"

    id = sa.Column(sa.Integer, primary_key=True)
    value = sa.Column('value', JsonTypeGzipped, nullable=True)
    points = sa.Column('points', sa.Integer, nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))
    # review comes from Review relationship
    key_id = sa.Column('key_id', sa.Integer, sa.ForeignKey('keys.id'))

    domain_id = sa.Column('domain_id', sa.Integer, sa.ForeignKey('domains.id'))

    review_is_active = sa.Column('review_is_active', sa.Boolean, default=True, nullable=False)

    def __str__(self):
        return '%s: %s' % (self.key.name, self.value)

    def __repr__(self):
        return str(self)

    def to_dict(self, violation_definitions):
        definition = violation_definitions.get(self.key.name, {})

        return {
            'key': self.key.name,
            'title': definition.get('title', 'undefined'),
            'description': definition.get('description', lambda value: value)(self.value),
            'points': self.points,
            'category': definition.get('category', 'undefined')
        }

    @classmethod
    def get_most_common_violations_names(cls, db, sample_limit=50000):
        sample = db \
            .query(
                Violation.id,
                Violation.key_id,
                Key.name.label('key_name')
            ) \
            .filter(Violation.key_id == Key.id) \
            .filter(Violation.review_is_active == True) \
            .order_by(Violation.id.desc()) \
            .limit(sample_limit) \
            .subquery()

        return db \
            .query(
                sample.columns.key_name,
                sa.func.count(sample.columns.key_id).label('count')
            ) \
            .group_by(sample.columns.key_id) \
            .order_by('count desc').all()

    @classmethod
    def get_most_common_violations(cls, db, violation_definitions, sample_limit=50000):
        violations = []

        for key_name, count in cls.get_most_common_violations_names(db, sample_limit):
            definition = violation_definitions.get(key_name, {})
            violations.append({
                "key": key_name,
                "title": definition.get('title', 'undefined'),
                "category": definition.get('category', 'undefined'),
                "count": count
            })

        return violations

    @classmethod
    def get_by_key_id_group_by_domain(cls, db, key_id):

        from holmes.models.violation import Violation  # to avoid circular dependency
        from holmes.models.domain import Domain  # to avoid circular dependency

        return db \
            .query(
                Domain.name.label('domain_name'),
                sa.func.count(Violation.id).label('violation_count')
            ) \
            .filter(Domain.id == Violation.domain_id) \
            .filter(Violation.key_id == key_id) \
            .filter(Violation.review_is_active == True) \
            .group_by(Domain.id) \
            .order_by('violation_count DESC') \
            .all()

    @classmethod
    def get_group_by_category_id_for_all_domains(cls, db):
        from holmes.models.keys import Key  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency

        data = db \
            .query(
                Violation.domain_id,
                Key.name,
                Key.category_id,
                sa.func.count(Key.category_id).label('violation_count')
            ) \
            .filter(Key.id == Violation.key_id) \
            .filter(Violation.review_is_active == True) \
            .group_by(Violation.domain_id) \
            .group_by(Key.category_id) \
            .order_by('violation_count DESC') \
            .all()

        result = defaultdict(list)

        for item in data:
            result[item.domain_id].append({
                'key_name': item.name,
                'category_id': item.category_id,
                'violation_count': item.violation_count
            })

        return result

    @classmethod
    def get_group_by_value_for_key(cls, db, key_name):
        from holmes.models.keys import Key  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency

        return db \
            .query(
                Violation.value,
                sa.func.count(Violation.key_id).label('count')
            ) \
            .filter(Key.name == key_name) \
            .filter(Key.id == Violation.key_id) \
            .filter(Violation.review_is_active == True) \
            .group_by(Violation.value) \
            .order_by('count DESC') \
            .all()

    @classmethod
    def get_top_in_category_for_domain(cls, db, domain, key_category_id, limit=10):
        from holmes.models.keys import Key  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency

        return db \
            .query(
                Key.name,
                sa.func.count(Key.category_id).label('violation_count')
            ) \
            .filter(Key.id == Violation.key_id) \
            .filter(Violation.domain_id == domain.id) \
            .filter(Violation.review_is_active == True) \
            .filter(Key.category_id == key_category_id) \
            .group_by(Key.id) \
            .order_by('violation_count DESC') \
            .limit(limit) \
            .all()
