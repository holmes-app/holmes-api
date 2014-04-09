#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import math

import sqlalchemy as sa

from holmes.models import Base


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
    def get_all(cls, db):
        return db \
            .query(Limiter) \
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

    @classmethod
    def _get_limiter_for_url(cls, limiters, url):
        for limiter in limiters:
            if limiter.matches(url):
                return limiter

        return None

    @classmethod
    def has_limit_to_work(cls, db, cache, active_domains, url, avg_links_per_page=10):
        if avg_links_per_page < 1:
            avg_links_per_page = 1

        limiters = Limiter.get_limiters_for_domains(db, active_domains)

        limiter = Limiter._get_limiter_for_url(limiters, url)

        if limiter:
            worker_count = cache.get_limit_usage(limiter.url)

            if worker_count >= math.ceil(float(limiter.value) / float(avg_links_per_page)):
                return False

        return True
