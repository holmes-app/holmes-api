#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from tests.unit.base import ApiTestCase
from tests.fixtures import (
    DomainsViolationsPrefsFactory, DomainFactory, KeyFactory
)
from holmes.models import DomainsViolationsPrefs, Key, Domain, KeysCategory


class TestDomainsViolationsPrefs(ApiTestCase):
    @property
    def cache(self):
        return self.server.application.cache

    def tearDown(self):
        self.db.rollback()
        self.db.query(DomainsViolationsPrefs).delete()
        self.db.query(Domain).delete()
        self.db.query(Key).delete()
        self.db.query(KeysCategory).delete()
        self.db.commit()

        self.server.application.redis.flushdb()

        super(ApiTestCase, self).tearDown()

    def test_can_create_domains_violations_prefs(self):
        data = DomainsViolationsPrefsFactory.create(
            domain=Domain(name='globo.com'),
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        loaded = self.db.query(DomainsViolationsPrefs).get(data.id)

        expect(loaded.domain.name).to_equal('globo.com')
        expect(loaded.key.name).to_equal('some.random.fact')
        expect(loaded.value).to_equal('whatever')

    def test_can_convert_to_dict(self):
        data = DomainsViolationsPrefsFactory.create(
            domain=Domain(name='globo.com'),
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        expect(data.to_dict()).to_be_like({
            'domain': 'globo.com',
            'key': 'some.random.fact',
            'value': 'whatever',
        })

    def test_domains_violations_prefs_str(self):
        data = DomainsViolationsPrefsFactory.create(
            domain=Domain(name='globo.com'),
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        loaded = self.db.query(DomainsViolationsPrefs).get(data.id)

        expect(str(loaded)).to_be_like('some.random.fact (globo.com): whatever')

    def test_can_get_all_domains_violations_prefs(self):
        pref1 = DomainsViolationsPrefsFactory.create(value='whatever')
        pref2 = DomainsViolationsPrefsFactory.create(value='{"test": 10}')
        pref3 = DomainsViolationsPrefsFactory.create(value='["holmes", "ab"]')

        data = DomainsViolationsPrefs.get_all_domains_violations_prefs(self.db)

        expect(data).not_to_be_null()
        expect(data).to_length(3)
        expect(data[0]).to_equal(pref1)
        expect(data[1]).to_equal(pref2)
        expect(data[2]).to_equal(pref3)

    def test_can_get_domains_violations_prefs(self):
        data = DomainsViolationsPrefsFactory.create(
            domain=Domain(name='globo.com'),
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        data = DomainsViolationsPrefs.get_domains_violations_prefs(self.db)

        expect(data).to_be_like({
            'globo.com': {
                'some.random.fact': 'whatever'
            }
        })

    def test_can_insert_domains_violations_prefs(self):
        domain = DomainFactory.create()
        key = KeyFactory.create()
        value = '{"page.size": 100}'

        DomainsViolationsPrefs.insert_domains_violations_prefs(
            self.db, domain, key, value
        )

        data = self.db \
            .query(DomainsViolationsPrefs) \
            .filter(
                DomainsViolationsPrefs.key_id == key.id,
                DomainsViolationsPrefs.domain_id == domain.id,
            ) \
            .all()

        expect(data).not_to_be_null()
        expect(data).to_length(1)
        expect(data[0].value).to_equal(value)

    def test_can_insert_default_violations_values_for_domain(self):
        domain = DomainFactory.create()

        page_title_size = KeyFactory.create(name='page.title.size')
        total_requests_img = KeyFactory.create(name='total.requests.img')

        violation_definitions = {
            'page.title.size': {'key': page_title_size, 'default_value': 100},
            'total.requests.img': {'key': total_requests_img, 'default_value': 5}
        }

        keys = violation_definitions.keys()

        data = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)
        expect(data).to_length(0)

        DomainsViolationsPrefs.insert_default_violations_values_for_domain(
            self.db,
            domain,
            keys,
            violation_definitions,
            self.cache
        )

        data = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)

        expect(data).not_to_be_null()
        expect(data).to_length(2)
        expect(data).to_be_like([
            {'value': 100, 'key': 'page.title.size'},
            {'value': 5, 'key': 'total.requests.img'}
        ])

    def test_can_insert_default_violations_values_for_all_domains(self):
        DomainsViolationsPrefsFactory.create(
            domain=Domain(name='globo.com'),
            key=Key(name='some.random.fact'),
            value='whatever'
        )

        for x in range(3):
            DomainFactory.create(name='g%d.com' % x)

        domains_violations_prefs = \
            DomainsViolationsPrefs.get_domains_violations_prefs(self.db)

        expect(domains_violations_prefs).to_length(1)

        default_violations_values = {
            'page.title.size': 100,
            'total.requests.img': 5,
        }

        page_title_size = KeyFactory.create(name='page.title.size')
        total_requests_img = KeyFactory.create(name='total.requests.img')

        violation_definitions = {
            'page.title.size': {'key': page_title_size, 'default_value': 100},
            'total.requests.img': {'key': total_requests_img, 'default_value': 5}
        }

        DomainsViolationsPrefs.insert_default_violations_values_for_all_domains(
            self.db,
            default_violations_values,
            violation_definitions,
            self.cache
        )

        domains_violations_prefs = \
            DomainsViolationsPrefs.get_domains_violations_prefs(self.db)

        expect(domains_violations_prefs).to_length(4)

        expect(domains_violations_prefs).to_be_like({
            'globo.com': {
                'some.random.fact': 'whatever',
                'total.requests.img': 5,
                'page.title.size': 100
            },
            'g0.com': {'page.title.size': 100, 'total.requests.img': 5},
            'g1.com': {'page.title.size': 100, 'total.requests.img': 5},
            'g2.com': {'page.title.size': 100, 'total.requests.img': 5},
        })

    def test_can_update_by_domain(self):
        domain = DomainFactory.create(name='globo.com')

        DomainsViolationsPrefsFactory.create(
            domain=domain,
            key=Key(name='some.random'),
            value='whatever'
        )

        loaded = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)

        expect(loaded).not_to_be_null()
        expect(loaded).to_length(1)
        expect(loaded).to_be_like([{'key': 'some.random', 'value': 'whatever'}])

        data = [
            {'key': 'some.random', 'value': '10'},
            {'invalid_key': 'some.random.1', 'invalid_value': '101'}
        ]

        DomainsViolationsPrefs.update_by_domain(self.db, self.cache, domain, data)

        loaded = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)

        expect(loaded).not_to_be_null()
        expect(loaded).to_length(1)
        expect(loaded).to_be_like([{'key': 'some.random', 'value': '10'}])

    def test_can_update_by_domain_with_empty_data(self):
        domain = DomainFactory.create(name='globo.com')

        data = []

        DomainsViolationsPrefs.update_by_domain(self.db, self.cache, domain, data)

        loaded = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)

        expect(loaded).to_equal([])
