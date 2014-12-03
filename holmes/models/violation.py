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

    def to_dict(self, violation_definitions, _):
        definition = violation_definitions.get(self.key.name, {})

        value = definition.get('value_parser', lambda val: val)(self.value)
        description = _(definition.get('description', '%s'))

        if value:
            try:
                description = (description % value)
            except TypeError:
                pass

        return {
            'key': self.key.name,
            'title': _(definition.get('title', _('undefined'))),
            'description': description,
            'points': self.points,
            'category': _(definition.get('category', _('undefined')))
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
    def get_group_by_key_id_for_all_domains(cls, db):

        from holmes.models.violation import Violation  # to avoid circular dependency
        from holmes.models.domain import Domain  # to avoid circular dependency

        sample = db \
            .query(
                Violation.key_id.label('violations_key_id'),
                Violation.domain_id,
                sa.func.count(Violation.id).label('violation_count')
            ) \
            .filter(Violation.review_is_active == True) \
            .group_by(Violation.domain_id, Violation.key_id) \
            .subquery()

        return db \
            .query(
                sample.columns.violations_key_id,
                Domain.name.label('domain_name'),
                sample.columns.violation_count
            ) \
            .filter(Domain.id == sample.columns.domain_id) \
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
    def get_top_in_category_for_all_domains(cls, db, limit=1000):
        from holmes.models.keys import Key  # to avoid circular dependency
        from holmes.models.domain import Domain  # to avoid circular dependency
        from holmes.models.violation import Violation  # to avoid circular dependency

        sample = db \
            .query(
                Violation.key_id.label('violations_key_id'),
                Violation.domain_id,
                sa.func.count(Violation.id).label('violation_count')
            ) \
            .filter(Violation.review_is_active == True) \
            .group_by(Violation.domain_id, Violation.key_id) \
            .subquery()

        return db \
            .query(
                Domain.name,
                Key.category_id,
                Key.name,
                sample.columns.violation_count
            ) \
            .filter(sample.columns.domain_id == Domain.id) \
            .filter(sample.columns.violations_key_id == Key.id) \
            .group_by(
                sample.columns.domain_id,
                sample.columns.violations_key_id,
                Key.category_id
            ) \
            .order_by('violation_count DESC') \
            .limit(limit) \
            .all()
