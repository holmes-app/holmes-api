#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

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
    def get_by_name(cls, db, category_name):
        try:
            result = db \
                .query(KeysCategory) \
                .filter(KeysCategory.name == category_name) \
                .one()
        except NoResultFound:
            result = None

        return result

    @classmethod
    def get_or_create(cls, db, category_name):
        category = cls.get_by_name(db, category_name)

        if category is not None:
            return category

        query_params = {'name': category_name}

        db.execute(
            'INSERT INTO `keys_category` (name) ' \
            'VALUES (:name) ON DUPLICATE KEY ' \
            'UPDATE name = :name',
            query_params
        )

        return cls.get_by_name(db, category_name)
