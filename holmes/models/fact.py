#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base, JsonTypeGzipped


class Fact(Base):
    __tablename__ = "facts"

    id = sa.Column(sa.Integer, primary_key=True)

    value = sa.Column('value', JsonTypeGzipped, nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))
    # review comes from Review relationship

    key_id = sa.Column('key_id', sa.Integer, sa.ForeignKey('keys.id'))

    def to_dict(self, fact_definitions):
        definition = fact_definitions.get(self.key.name, {})
        return {
            'title': definition.get('title', 'unknown'),
            'key': self.key.name,
            'unit': definition.get('unit', 'value'),
            'value': definition.get('description', lambda value: value)(self.value),
            'category': definition.get('category', 'unknown')
        }

    def __str__(self):
        return '%s: %s' % (self.key.name, self.value)

    def __repr__(self):
        return str(self)
