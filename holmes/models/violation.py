#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base, JsonType


class Violation(Base):
    __tablename__ = "violations"

    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column('key', sa.String(2000), nullable=False)
    value = sa.Column('value', JsonType, nullable=False)
    #title = sa.Column('title', sa.String(2000), nullable=False)
    #description = sa.Column('description', sa.Text, nullable=False)
    points = sa.Column('points', sa.Integer, nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))

    def __str__(self):
        return '%s: %s' % (self.key, self.value)

    def __repr__(self):
        return str(self)

    def to_dict(self, violation_definitions):
        return {
            'key': self.key,
            'title': violation_definitions[self.key]['title'],
            'description': violation_definitions[self.key]['description'](self.value),
            'points': self.points
        }

    @classmethod
    def get_most_common_violations(cls, db, violation_definitions, limit=5):
        violations = []
        results = db.query(Violation.key, sa.func.count(Violation.id).label('count')) \
                    .group_by(Violation.key) \
                    .order_by('count desc')[:limit]

        for item in results:
            violations.append({
                "key": item.key,
                "title": violation_definitions[item.key]['title'],
                "count": item.count
            })

        return violations
