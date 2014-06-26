#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from tests.unit.base import ApiTestCase
from tests.fixtures import UsersViolationsPrefsFactory, UserFactory, KeyFactory
from holmes.models import UsersViolationsPrefs, User, Key


class TestUsersViolationsPrefs(ApiTestCase):

    def test_can_create_users_violations_prefs(self):
        data = UsersViolationsPrefsFactory.create(
            user=User(email='sherlock@holmes.com', fullname='Sherlock Holmes'),
            key=Key(name='some.random.fact'),
            is_active=False
        )

        loaded = self.db.query(UsersViolationsPrefs).get(data.id)

        expect(loaded.user.email).to_equal('sherlock@holmes.com')
        expect(loaded.key.name).to_equal('some.random.fact')
        expect(loaded.is_active).to_equal(False)

    def test_can_convert_to_dict(self):
        data = UsersViolationsPrefsFactory.create(
            user=User(email='sherlock@holmes.com', fullname='Sherlock Holmes'),
            key=Key(name='some.random.fact'),
            is_active=False
        )

        expect(data.to_dict()).to_be_like({
            'user': 'sherlock@holmes.com',
            'key': 'some.random.fact',
            'is_active': False
        })

    def test_users_violations_prefs_str(self):
        data = UsersViolationsPrefsFactory.create(
            user=User(email='sherlock@holmes.com', fullname='Sherlock Holmes'),
            key=Key(name='some.random.fact'),
            is_active=False
        )

        loaded = self.db.query(UsersViolationsPrefs).get(data.id)

        expect(str(loaded)).to_be_like('sherlock@holmes.com: some.random.fact')

    def test_can_get_prefs(self):
        user = UserFactory.create()
        key1 = KeyFactory.create()
        key2 = KeyFactory.create()

        UsersViolationsPrefs.insert_pref(self.db, user, key1, True)
        UsersViolationsPrefs.insert_pref(self.db, user, key2, False)

        data = UsersViolationsPrefs.get_prefs(self.db, user)

        expect(data).to_length(2)

        expect(data).to_be_like(
            {key1.name: True, key2.name: False}
        )

    def test_can_insert_pref(self):
        user = UserFactory.create()
        key1 = KeyFactory.create()
        key2 = KeyFactory.create()

        UsersViolationsPrefs.insert_pref(self.db, user, key1, True)
        UsersViolationsPrefs.insert_pref(self.db, user, key2, False)

        prefs = self.db.query(UsersViolationsPrefs).all()

        expect(prefs).to_length(2)

        expect(prefs[0].key).to_equal(key1)
        expect(prefs[0].user).to_equal(user)
        expect(prefs[0].is_active).to_equal(True)

        expect(prefs[1].key).to_equal(key2)
        expect(prefs[1].user).to_equal(user)
        expect(prefs[1].is_active).to_equal(False)

    def test_can_update_by_user(self):
        user = UserFactory.create()

        key = KeyFactory.create(name='some.random')

        pref = UsersViolationsPrefsFactory.create(user=user, key=key, is_active=True)

        data = [
            {'key': pref.key.name, 'is_active': False},
            {'key': 'blah', 'is_active': False}
        ]

        UsersViolationsPrefs.update_by_user(self.db, user, data)

        prefs = self.db.query(UsersViolationsPrefs).all()

        expect(prefs).to_length(1)
        expect(prefs[0].key.name).to_equal(key.name)
        expect(prefs[0].user).to_equal(user)
        expect(prefs[0].is_active).to_equal(False)

    def test_can_update_by_user_with_no_data(self):
        user = UserFactory.create()

        key = KeyFactory.create(name='some.random')

        UsersViolationsPrefsFactory.create(user=user, key=key, is_active=True)

        data = []

        UsersViolationsPrefs.update_by_user(self.db, user, data)

        prefs = self.db.query(UsersViolationsPrefs).all()

        expect(prefs).to_length(1)
        expect(prefs[0].key.name).to_equal(key.name)
        expect(prefs[0].user).to_equal(user)
        expect(prefs[0].is_active).to_equal(True)

    def test_can_delete_prefs(self):
        user = UserFactory.create()

        pref1 = UsersViolationsPrefsFactory.create(user=user)
        pref2 = UsersViolationsPrefsFactory.create(user=user)

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(2)

        items = [pref1.key.name]

        UsersViolationsPrefs.delete_prefs(self.db, user, items)

        prefs = self.db.query(UsersViolationsPrefs).all()

        expect(prefs).to_length(1)
        expect(prefs[0].key.name).to_equal(pref2.key.name)
        expect(prefs[0].user).to_equal(pref2.user)
        expect(prefs[0].is_active).to_equal(True)

    def test_can_insert_prefs(self):
        user = UserFactory.create()

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(0)

        items = []
        for x in range(3):
            name = 'key-test-%d' % x
            KeyFactory.create(name=name)
            items.append(name)

        UsersViolationsPrefs.insert_prefs(self.db, user, items)

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(3)

    def test_can_insert_prefs_without_user(self):
        user = None

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(0)

        items = []
        for x in range(3):
            name = 'key-test-%d' % x
            KeyFactory.create(name=name)
            items.append(name)

        UsersViolationsPrefs.insert_prefs(self.db, user, items)

        prefs = self.db.query(UsersViolationsPrefs).all()
        expect(prefs).to_length(0)
