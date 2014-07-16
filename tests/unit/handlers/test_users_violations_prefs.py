#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads, dumps

from tests.fixtures import (
    UsersViolationsPrefsFactory, KeyFactory, UserFactory
)
from tests.unit.base import ApiTestCase
from holmes.models import UsersViolationsPrefs


class TestUsersViolationsPrefsHandler(ApiTestCase):

    @gen_test
    def test_can_get_prefs(self):
        user = UserFactory.create()

        key1 = KeyFactory.create(name='some.random.1')
        key2 = KeyFactory.create(name='some.random.2')

        UsersViolationsPrefsFactory.create(user=user, key=key1, is_active=True)
        UsersViolationsPrefsFactory.create(user=user, key=key2, is_active=False)

        self.server.application.violation_definitions = {
            'some.random.1': {
                'title': 'some random 1',
                'category': 'SEO',
                'generic_description': 'my some random 1'
            },
            'some.random.2': {
                'title': 'some random 2',
                'category': 'HTTP',
                'generic_description': 'my some random 2'
            }
        }

        response = yield self.authenticated_fetch(
            '/users/violations-prefs/',
            user_email=user.email
        )

        expect(response.code).to_equal(200)

        prefs = loads(response.body)

        expect(prefs).to_length(2)
        expect(prefs[0]).to_length(5)
        expect(prefs[1]).to_length(5)

        expect(prefs).to_be_like([{
            'category': 'SEO',
            'is_active': True,
            'name': 'some random 1',
            'key': u'some.random.1',
            'description': u'my some random 1'
        }, {
            'category': 'HTTP',
            'is_active': False,
            'name': 'some random 2',
            'key': u'some.random.2',
            'description': u'my some random 2'
        }])

    @gen_test
    def test_can_get_prefs_with_remove_violation_definitions(self):
        user = UserFactory.create()

        key1 = KeyFactory.create(name='some.random.1')
        key2 = KeyFactory.create(name='some.random.2')

        UsersViolationsPrefsFactory.create(user=user, key=key1, is_active=True)
        UsersViolationsPrefsFactory.create(user=user, key=key2, is_active=False)

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(2)

        self.server.application.violation_definitions = {
            'some.random.1': {
                'title': 'some random 1',
                'category': 'SEO',
                'generic_description': 'my some random 1'
            }
        }

        response = yield self.authenticated_fetch(
            '/users/violations-prefs/',
            user_email=user.email
        )

        expect(response.code).to_equal(200)

        prefs = loads(response.body)

        expect(prefs).to_length(1)
        expect(prefs).to_be_like([{
            'category': 'SEO',
            'is_active': True,
            'name': 'some random 1',
            'key': u'some.random.1',
            'description': u'my some random 1'
        }])

    @gen_test
    def test_can_get_prefs_with_insert_violation_definitions(self):
        user = UserFactory.create()

        key1 = KeyFactory.create(name='some.random.1')
        KeyFactory.create(name='some.random.2')

        UsersViolationsPrefsFactory.create(user=user, key=key1, is_active=True)

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(1)

        self.server.application.violation_definitions = {
            'some.random.1': {
                'title': 'some random 1',
                'category': 'SEO',
                'generic_description': 'my some random 1'
            },
            'some.random.2': {
                'title': 'some random 2',
                'category': 'HTTP',
                'generic_description': 'my some random 2'
            },
        }

        response = yield self.authenticated_fetch(
            '/users/violations-prefs/',
            user_email=user.email
        )

        expect(response.code).to_equal(200)

        prefs = loads(response.body)

        expect(prefs).to_length(2)
        expect(prefs).to_be_like([{
            'category': 'SEO',
            'is_active': True,
            'name': 'some random 1',
            'key': u'some.random.1',
            'description': u'my some random 1'
        }, {
            'category': 'HTTP',
            'is_active': True,
            'name': 'some random 2',
            'key': u'some.random.2',
            'description': u'my some random 2'
        }])

    @gen_test
    def test_can_save_prefs(self):
        user = UserFactory.create(is_superuser=True)

        key1 = KeyFactory.create(name='some.random.1')
        key2 = KeyFactory.create(name='some.random.2')

        UsersViolationsPrefsFactory.create(user=user, key=key1, is_active=True)
        UsersViolationsPrefsFactory.create(user=user, key=key2, is_active=False)

        loaded_prefs = UsersViolationsPrefs.get_prefs(self.db, user)
        expect(loaded_prefs).to_length(2)
        expect(loaded_prefs).to_be_like({
            'some.random.1': True,
            'some.random.2': False
        })

        yield self.authenticated_fetch(
            '/users/violations-prefs/',
            user_email=user.email,
            method='POST',
            body=dumps([
                {'key': 'some.random.1', 'is_active': False},
                {'key': 'some.random.2', 'is_active': True},
            ])
        )

        loaded_prefs = UsersViolationsPrefs.get_prefs(self.db, user)
        expect(loaded_prefs).to_length(2)
        expect(loaded_prefs).to_be_like({
            'some.random.1': False,
            'some.random.2': True
        })

    @gen_test
    def test_can_get_prefs_as_anonymous(self):
        try:
            yield self.anonymous_fetch(
                '/users/violations-prefs/',
                method='GET'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_prefs_as_anonymous(self):
        try:
            yield self.anonymous_fetch(
                '/users/violations-prefs/',
                method='POST',
                body=dumps([
                    {'key': 'some.random.1', 'is_active': False},
                    {'key': 'some.random.2', 'is_active': True},
                ])
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'
