#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base


class Key(Base):
    __tablename__ = "keys"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column('name', sa.String(2000), nullable=False)

    category_id = sa.Column(
        'category_id',
        sa.Integer,
        sa.ForeignKey('keys_category.id')
    )

    facts = relationship("Fact", cascade="all,delete", backref="key")
    violations = relationship("Violation", cascade="all,delete", backref="key")

    def __str__(self):
        return '%s' % (self.name)

    def __repr__(self):
        return str(self)

    @classmethod
    def get_or_create(cls, db, key_name):
        key = db.query(Key).filter(Key.name == key_name).scalar()

        if not key:
            key = Key(name=key_name)

        return key
