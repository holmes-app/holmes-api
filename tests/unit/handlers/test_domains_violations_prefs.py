#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads, dumps
from mock import Mock

from tests.unit.base import ApiTestCase

from tests.fixtures import (
    DomainFactory, DomainsViolationsPrefsFactory, KeyFactory, UserFactory
)
from holmes.models import (
    DomainsViolationsPrefs, Key, KeysCategory, Domain, User
)


class TestDomainsViolationsPrefsHandler(ApiTestCase):
    def tearDown(self):
        self.db.rollback()
        self.db.query(DomainsViolationsPrefs).delete()
        self.db.query(Domain).delete()
        self.db.query(Key).delete()
        self.db.query(KeysCategory).delete()
        self.db.query(User).delete()
        self.db.commit()

        self.server.application.redis.flushdb()

        super(ApiTestCase, self).tearDown()

    def mock_request(self, code, body):
        def handle(*args, **kw):
            response_mock = Mock(code=code, body=body)
            if 'callback' in kw:
                kw['callback'](response_mock)
            else:
                args[-1](response_mock)

        client = Mock()
        self.server.application.http_client = client
        client.fetch.side_effect = handle

    @gen_test
    def test_can_get_prefs_for_invalid_domain(self):
        try:
            user = UserFactory()
            user_data = dumps(user.to_dict())

            self.mock_request(code=200, body=user_data)

            yield self.authenticated_fetch('/domains/blah.com/violations-prefs/')
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_equal('Domain blah.com not found')

    @gen_test
    def test_can_get_prefs(self):
        domain = DomainFactory.create(name='globo.com')

        key1 = KeyFactory.create(name='some.random.1')
        key2 = KeyFactory.create(name='some.random.2')

        DomainsViolationsPrefsFactory.create(domain=domain, key=key1, value=100)
        DomainsViolationsPrefsFactory.create(domain=domain, key=key2, value=2)

        self.server.application.violation_definitions = {
            'some.random.1': {
                'category': 'SEO',
                'default_value': 100,
                'default_value_description': 'My some.random.1',
                'unit': 'number'
            },
            'some.random.2': {
                'category': 'HTTP',
                'default_value': 2,
                'default_value_description': 'My some.random.2',
                'unit': 'number'
            },
        }

        response = yield self.authenticated_fetch(
            '/domains/%s/violations-prefs/' % domain.name
        )

        expect(response.code).to_equal(200)

        prefs = loads(response.body)

        expect(prefs).to_length(2)
        expect(prefs[0]).to_length(6)
        expect(prefs[1]).to_length(6)

        expect(prefs).to_be_like([
            {
                'category': 'SEO',
                'default_value': 100,
                'title': 'My some.random.1',
                'value': 100,
                'key': 'some.random.1',
                'unit': 'number'
            },{
                'category': 'HTTP',
                'default_value': 2,
                'title': 'My some.random.2',
                'value': 2,
                'key': 'some.random.2',
                'unit': 'number'
            }
        ])

    @gen_test
    def test_can_get_prefs_with_invalid_violation_definition(self):
        domain = DomainFactory.create(name='globo.com')

        key = KeyFactory.create(name='some.random.1')
        DomainsViolationsPrefsFactory.create(domain=domain, key=key)

        self.server.application.violation_definitions = {}

        response = yield self.authenticated_fetch(
            '/domains/%s/violations-prefs/' % domain.name
        )

        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_length(0)

    @gen_test
    def test_can_save_prefs_with_access_token(self):
        domain = DomainFactory.create(name='globo.com')

        key = KeyFactory.create(name='some.random')

        DomainsViolationsPrefsFactory.create(domain=domain, key=key, value=100)

        loaded_prefs = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)
        expect(loaded_prefs).to_length(1)
        expect(loaded_prefs[0]).to_be_like({
            'value': 100,
            'key': 'some.random'
        })

        user = UserFactory()
        user_data = dumps(user.to_dict())

        self.mock_request(code=200, body=user_data)

        yield self.authenticated_fetch(
            '/domains/%s/violations-prefs/' % domain.name,
            method='POST',
            body=dumps([
                {'key': 'some.random', 'value': 10},
            ])
        )

        loaded_prefs = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(self.db, domain.name)
        expect(loaded_prefs).to_length(1)
        expect(loaded_prefs[0]).to_be_like({
            'value': 10,
            'key': 'some.random'
        })

    @gen_test
    def test_can_save_prefs_for_invalid_domain(self):
        user = UserFactory()
        user_data = dumps(user.to_dict())

        self.mock_request(code=200, body=user_data)

        try:
            yield self.authenticated_fetch(
                '/domains/blah.com/violations-prefs/',
                method='POST',
                body=dumps([
                    {'key': 'some.random', 'value': 10},
                ])
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_equal('Domain blah.com not found')

    @gen_test
    def test_can_save_prefs_without_access_token(self):
        try:
            yield self.anonymous_fetch(
                '/domains/blah.com/violations-prefs/',
                method='POST',
                body=dumps([
                    {'key': 'some.random', 'value': 10},
                ])
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(401)
            expect(err.response.reason).to_equal('Unauthorized')

    @gen_test
    def test_can_save_prefs_with_not_authorized_user(self):
        # TODO: this test need an refactory on the User business model
        # we need to provide a @decorator to handlers get/post/etc functions
        # to check user permissions, and then can test something like that
        pass
        #try:
            #yield self.anonymous_fetch(
                #'/domains/blah.com/violations-prefs/',
                #method='POST',
                #body=dumps([
                    #{'key': 'some.random', 'value': 10},
                #])
            #)
        #except HTTPError:
            #err = sys.exc_info()[1]
            #expect(err).not_to_be_null()
            #expect(err.code).to_equal(401)
            #expect(err.response.reason).to_be_like('Unauthorized')
            #expect(err.response.body).to_be_like('Unauthorized')
        #else:
            #assert False, 'Should not have got this far'
