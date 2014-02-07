#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import sqlalchemy as sa

from holmes.models import Base


class Delimiter(Base):
    __tablename__ = "delimiters"

    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column('url', sa.String(2000), nullable=False)
    url_hash = sa.Column('url_hash', sa.String(128), nullable=False)
    value = sa.Column('value', sa.Integer, server_default='1', nullable=False)

    def to_dict(self):
        return {
            'url': self.url,
            'value': self.value
        }

    def __str__(self):
        return str(self.url)

    def __repr__(self):
        return str(self)

    @classmethod
    def get_all(cls, db):
        return db \
            .query(Delimiter) \
            .order_by(sa.func.char_length(Delimiter.url)) \
            .all()

    @classmethod
    def by_url(cls, url, db):
        return db.query(Delimiter).filter(Delimiter.url==url).first()

    @classmethod
    def by_url_hash(cls, url_hash, db):
        return db.query(Delimiter).filter(Delimiter.url_hash==url_hash).first()

    @classmethod
    def add_or_update_delimiter(cls, db, url, value):
        url = url.encode('utf-8')
        url_hash = hashlib.sha512(url).hexdigest()
        delimiter = Delimiter.by_url_hash(url_hash, db)

        if delimiter:
            db \
                .query(Delimiter) \
                .filter(Delimiter.id == delimiter.id) \
                .update({'value': value})

            db.flush()
            db.commit()

            return delimiter.url

        db.begin(subtransactions=True)
        delimiter = Delimiter(url=url, url_hash=url_hash, value=value)
        db.add(delimiter)
        db.flush()
        db.commit()

        return delimiter.url
