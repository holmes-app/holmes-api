#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

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
    def get_by_name(cls, db, key_name):
        try:
            result = db.query(Key).filter(Key.name == key_name).one()
        except NoResultFound:
            result = None

        return result

    @classmethod
    def get_or_create(cls, db, key_name, category_name=None):
        key = cls.get_by_name(db, key_name)

        if key is not None:
            return key

        if category_name is None:
            query_params = {'name': key_name}

            db.execute(
                'INSERT INTO `keys` (name) ' \
                'VALUES (:name) ON DUPLICATE KEY ' \
                'UPDATE name = :name',
                query_params
            )
        else:
            from holmes.models import KeysCategory
            category = KeysCategory.get_or_create(db, category_name)

            query_params = {'name': key_name, 'category_id': category.id}

            db.execute(
                'INSERT INTO `keys` (name, category_id) ' \
                'VALUES (:name, :category_id) ON DUPLICATE KEY ' \
                'UPDATE name = :name, category_id = :category_id',
                query_params
            )

        return cls.get_by_name(db, key_name)
