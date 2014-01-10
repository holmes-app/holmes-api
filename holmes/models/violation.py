#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base, JsonType
from holmes.models.keys import Key


class Violation(Base):
    __tablename__ = "violations"

    id = sa.Column(sa.Integer, primary_key=True)
    value = sa.Column('value', JsonType, nullable=True)
    points = sa.Column('points', sa.Integer, nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))
    # review comes from Review relationship
    key_id = sa.Column('key_id', sa.Integer, sa.ForeignKey('keys.id'))

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
            'points': self.points
        }

    @classmethod
    def get_most_common_violations(cls, db, violation_definitions, limit=5):
        violations = []

        results = db.query(Violation.key_id, Key.name, sa.func.count(Violation.id).label('count')) \
                    .outerjoin(Key) \
                    .group_by(Violation.key_id) \
                    .order_by('count desc') \
                    .limit(limit)

        for key_id, key_name, count in results:
            definition = violation_definitions.get(key_name, {})
            violations.append({
                "key": key_name,
                "title": definition.get('title', 'undefined'),
                "count": count
            })

        return violations
