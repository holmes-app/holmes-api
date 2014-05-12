#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib

import sqlalchemy as sa

from holmes.models import Base
from holmes.models.domain import Domain

class Limiter(Base):
    __tablename__ = "limiters"

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
    def get_all(cls, db, domain_filter=None):
        query = db.query(Limiter)

        if domain_filter:
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                query = query.filter(Limiter.url.startswith(domain.url))

        return query \
               .order_by(sa.func.char_length(Limiter.url)) \
               .all()

    @classmethod
    def by_url(cls, url, db):
        return db.query(Limiter).filter(Limiter.url == url).first()

    @classmethod
    def by_url_hash(cls, url_hash, db):
        return db.query(Limiter).filter(Limiter.url_hash == url_hash).first()

    @classmethod
    def by_id(cls, id_, db):
        return db.query(Limiter).filter(Limiter.id == id_).first()

    @classmethod
    def delete(cls, id_, db):
        return db.query(Limiter).filter(Limiter.id == id_).delete()

    def matches(self, url):
        return url.startswith(self.url)

    @classmethod
    def add_or_update_limiter(cls, db, url, value):
        if not url:
            return

        url = url.encode('utf-8')
        url_hash = hashlib.sha512(url).hexdigest()
        limiter = Limiter.by_url_hash(url_hash, db)

        if limiter:
            db \
                .query(Limiter) \
                .filter(Limiter.id == limiter.id) \
                .update({'value': value})

            db.flush()
            db.commit()

            return limiter.url

        limiter = Limiter(url=url, url_hash=url_hash, value=value)
        db.add(limiter)

        return limiter.url

    @classmethod
    def get_limiters_for_domains(cls, db, active_domains):
        from holmes.models import Limiter  # Avoid circular dependency

        all_limiters = Limiter.get_all(db)

        limiters = []
        for limiter in all_limiters:
            for domain in active_domains:
                if limiter.matches(domain.url):
                    limiters.append(limiter)

        return limiters
