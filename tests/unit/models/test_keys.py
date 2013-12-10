#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tests.unit.base import ApiTestCase
from tests.fixtures import KeyFactory

from holmes.models import Key


class TestKey(ApiTestCase):
    def test_can_create_key(self):
        key = KeyFactory.create(name='some.random.key')

        loaded_key = self.db.query(Key).get(key.id)

        expect(loaded_key.name).to_equal('some.random.key')
        expect(str(loaded_key)).to_be_like('%s' % key.name)

    def test_can_get_or_create(self):
        self.db.query(Key).delete()

        # Create
        key1 = Key.get_or_create(self.db, 'some.random.key')
        expect(key1.name).to_equal('some.random.key')

        # Get
        key2 = Key.get_or_create(self.db, 'some.random.key')
        expect(key1.id).to_equal(key2.id)
