#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from collections import defaultdict

from holmes.models import Base, JsonType


class DomainsViolationsPrefs(Base):
    __tablename__ = "domains_violations_prefs"

    id = sa.Column(sa.Integer, primary_key=True)
    domain_id = sa.Column('domain_id', sa.Integer, sa.ForeignKey('domains.id'))
    key_id = sa.Column('key_id', sa.Integer, sa.ForeignKey('keys.id'))
    value = sa.Column('value', JsonType, nullable=True)

    def __str__(self):
        return '%s (%s): %s' % (self.key.name, self.domain.name, self.value)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            'domain': self.domain.name,
            'key': self.key.name,
            'value': self.value
        }

    @classmethod
    def get_all_domains_violations_prefs(cls, db):
        return db.query(DomainsViolationsPrefs).all()

    @classmethod
    def get_domains_violations_prefs(cls, db):
        data = cls.get_all_domains_violations_prefs(db)

        prefs = defaultdict(dict)

        for d in data:
            prefs[d.domain.name].update({d.key.name: d.value})

        return prefs

    @classmethod
    def get_domains_violations_prefs_by_domain(cls, db, domain_name):
        from holmes.models import Domain

        prefs = db \
            .query(DomainsViolationsPrefs) \
            .filter(
                Domain.id == DomainsViolationsPrefs.domain_id,
                Domain.name == domain_name
            ) \
            .all()

        result = []
        for pref in prefs:
            result.append({'key': pref.key.name, 'value': pref.value})
        return result

    @classmethod
    def insert_domains_violations_prefs(cls, db, domain, key, value):
        pref = DomainsViolationsPrefs(domain=domain, key=key, value=value)
        db.add(pref)
        db.flush()
        # FIXME
        db.commit()

    @classmethod
    def insert_default_violations_values_for_domain(cls, db, domain, keys, violation_definitions, cache):
        for key_name in keys:
            key = violation_definitions.get(key_name)['key']
            value = violation_definitions.get(key_name).get('default_value', None)
            DomainsViolationsPrefs.insert_domains_violations_prefs(
                db, domain, key, value
            )

        cache.delete_domain_violations_prefs(domain.name)

    @classmethod
    def insert_default_violations_values_for_all_domains(
        cls, db, default_violations_values, violation_definitions, cache):

        from holmes.models import Domain

        domains_violations_prefs = DomainsViolationsPrefs.get_domains_violations_prefs(db)

        domains = Domain.get_all_domains(db)

        for domain in domains:
            domain_data = domains_violations_prefs.get(domain.name, None)

            if domain_data:
                keys = set(default_violations_values.keys()) - set(domain_data.keys())
            else:
                keys = default_violations_values.keys()

            DomainsViolationsPrefs.insert_default_violations_values_for_domain(
                db,
                domain,
                keys,
                violation_definitions,
                cache
            )

    @classmethod
    def update_by_domain(cls, db, cache, domain, data):
        from holmes.models import Key

        if not domain or not data:
            return

        for item in data:
            if 'key' not in item or 'value' not in item:
                continue

            db \
                .query(DomainsViolationsPrefs) \
                .filter(
                    DomainsViolationsPrefs.domain_id == domain.id,
                    Key.name == item.get('key'),
                    Key.id == DomainsViolationsPrefs.key_id
                ) \
                .update(
                    {'value': item.get('value')},
                    synchronize_session='fetch'
                )

        db.flush()

        cache.delete_domain_violations_prefs(domain.name)
