#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base


class KeysCategory(Base):
    __tablename__ = "keys_category"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column('name', sa.String(255), nullable=False)

    keys = relationship("Key", cascade="all,delete", backref="category")

    def __str__(self):
        return '%s' % (self.name)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            'name': self.name
        }

    @classmethod
    def get_or_create(cls, db, category_name):
        category = db \
            .query(KeysCategory) \
            .filter(KeysCategory.name == category_name) \
            .scalar()

        if not category:
            category = KeysCategory(name=category_name)

        return category
