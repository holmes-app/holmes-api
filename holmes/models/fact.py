#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base, JsonType


class Fact(Base):
    __tablename__ = "facts"

    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column('key', sa.String(2000), nullable=False)
    value = sa.Column('value', JsonType, nullable=False)
    #title = sa.Column('title', sa.String(2000), nullable=False)
    #unit = sa.Column('unit', sa.String(2000), nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))

    def to_dict(self, fact_definitions):
        return {
            'title': fact_definitions[self.key]['title'],
            'key': self.key,
            'unit': fact_definitions[self.key].get('unit', 'value'),
            'value': self.value
        }

    def __str__(self):
        return '%s: %s' % (self.key, self.value)

    def __repr__(self):
        return str(self)
