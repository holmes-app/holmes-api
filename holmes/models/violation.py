#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base


class Violation(Base):
    __tablename__ = "violations"

    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column('key', sa.String(2000), nullable=False)
    title = sa.Column('title', sa.String(2000), nullable=False)
    description = sa.Column('description', sa.Text, nullable=False)
    points = sa.Column('points', sa.Integer, nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))

    def __str__(self):
        return '%s: %s (%d points)\n%s' % (self.key, self.title, self.points, self.description)

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'key': self.key,
            'title': self.title,
            'description': self.description,
            'points': self.points
        }

    @classmethod
    def get_most_common_violations(cls, db, limit=5):
        violations = []
        results = db.query(Violation.key, Violation.title, sa.func.count(Violation.id).label('count')) \
                    .group_by(Violation.key) \
                    .order_by('count desc')[:limit]

        for item in results:
            violations.append({
                "key": item.key,
                "title": item.title,
                "count": item.count
            })

        return violations
