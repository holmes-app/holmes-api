#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
from preggy import expect

from holmes.models import Limiter, Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import LimiterFactory, DomainFactory


class TestLimiter(ApiTestCase):

    def test_can_create_limiter(self):
        limiter = LimiterFactory.create(url='http://test.com/')

        expect(str(limiter)).to_be_like('%s' % limiter.url)

        expect(limiter.id).not_to_be_null()
        expect(limiter.url).to_equal('http://test.com/')
        expect(limiter.value).to_equal(10)

    def test_can_convert_user_to_dict(self):
        limiter = LimiterFactory.create()

        limiter_dict = limiter.to_dict()

        expect(limiter_dict['url']).to_equal(limiter.url)
        expect(limiter_dict['value']).to_equal(limiter.value)

    def test_can_get_limiter_by_url_hash(self):
        self.db.query(Limiter).delete()

        limiter = LimiterFactory.create(url='http://test.com/')

        url_hash = hashlib.sha512('http://test.com/').hexdigest()

        loaded_limiter = Limiter.by_url_hash(url_hash, self.db)
        expect(loaded_limiter.id).to_equal(limiter.id)

        invalid_limiter = Limiter.by_url_hash('00000000', self.db)
        expect(invalid_limiter).to_be_null()

    def test_can_get_limiter_by_url(self):
        self.db.query(Limiter).delete()

        limiter = LimiterFactory.create(url='http://test.com/')

        loaded_limiter = Limiter.by_url('http://test.com/', self.db)
        expect(loaded_limiter.id).to_equal(limiter.id)

        invalid_limiter = Limiter.by_url('http://test.com/1', self.db)
        expect(invalid_limiter).to_be_null()

    def test_can_get_limiter_by_id(self):
        limiter = LimiterFactory.create()

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter.id).to_equal(limiter.id)

        invalid_limiter = Limiter.by_id(-1, self.db)
        expect(invalid_limiter).to_be_null()

    def test_can_delete_one_limiter(self):
        limiter = LimiterFactory.create()

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter.id).to_equal(limiter.id)

        affected = Limiter.delete(limiter.id, self.db)
        expect(affected).to_equal(1)

        deleted_limiter = Limiter.by_id(limiter.id, self.db)
        expect(deleted_limiter).to_be_null()

    def test_can_get_all_limiters(self):
        self.db.query(Limiter).delete()

        limiter = LimiterFactory.create(url='http://test.com/')
        LimiterFactory.create()
        LimiterFactory.create()

        limiters = Limiter.get_all(self.db)

        expect(limiters).not_to_be_null()
        expect(limiters).to_length(3)
        expect(limiters).to_include(limiter)

        DomainFactory.create(name='test.com', url='http://test.com')
        limiters = Limiter.get_all(self.db, domain_filter='test.com')

        expect(limiters).not_to_be_null()
        expect(limiters).to_length(1)

    def test_can_add_or_update_limiter(self):
        self.db.query(Limiter).delete()

        limiters = Limiter.get_all(self.db)
        expect(limiters).to_equal([])

        # Add
        url = 'http://globo.com/'
        value = 2
        Limiter.add_or_update_limiter(self.db, url, value)
        limiter = Limiter.by_url(url, self.db)

        expect(limiter.value).to_equal(2)

        # Update
        url = 'http://globo.com/'
        value = 3
        Limiter.add_or_update_limiter(self.db, url, value)
        limiter = Limiter.by_url(url, self.db)

        expect(limiter.value).to_equal(3)

    def test_limiter_matches_url(self):
        limiter = LimiterFactory.create(url='http://test.com/')

        expect(limiter.matches('http://test.com/1.html')).to_be_true()
        expect(limiter.matches('http://test2.com/1.html')).to_be_false()


    def test_get_limiters_for_domains(self):
        self.db.query(Limiter).delete()
        self.db.query(Domain).delete()

        for i in range(2):
            DomainFactory.create()

        value = 2
        url = 'http://globo.com/'
        Limiter.add_or_update_limiter(self.db, url, value)

        DomainFactory.create(url=url, name='globo.com')

        active_domains = self.db.query(Domain).all()

        domains = Limiter.get_limiters_for_domains(self.db, active_domains)

        expect(domains).to_length(1)
        expect(str(domains[0])).to_equal(url)
