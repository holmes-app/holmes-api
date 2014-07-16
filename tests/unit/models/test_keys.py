#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tests.unit.base import ApiTestCase
from tests.fixtures import KeyFactory, KeysCategoryFactory

from holmes.models import Key


class TestKey(ApiTestCase):

    def tearDown(self):
        super(TestKey, self).tearDown()
        self.db.query(Key).delete()
        self.db.commit()

    def test_can_create_key(self):
        key = KeyFactory.create(name='some.random.key')

        loaded_key = self.db.query(Key).get(key.id)

        expect(loaded_key.name).to_equal('some.random.key')
        expect(str(loaded_key)).to_be_like('%s' % key.name)

    def test_can_get_or_create(self):
        # Create
        key1 = Key.get_or_create(self.db, 'some.random.key')
        expect(key1.name).to_equal('some.random.key')

        # Get
        key2 = Key.get_or_create(self.db, 'some.random.key')
        expect(key1.id).to_equal(key2.id)

    def test_can_add_category(self):
        key = KeyFactory.create(name='some.random.key')

        category = KeysCategoryFactory(name='SEO')

        key.category = category

        self.db.flush()

        loaded_category = self.db.query(Key).get(key.id).category

        expect(str(loaded_category.name)).to_be_like('%s' % category.name)
        expect(loaded_category.name).to_equal(category.name)

    def test_get_by_name(self):
        key = KeyFactory.create(name='some.random.key')

        loadded_key = Key.get_by_name(self.db, 'some.random.key')

        expect(key).to_equal(loadded_key)
        expect(loadded_key.name).to_equal('some.random.key')

    def test_can_insert_keys(self):
        default_values = {}
        keys = {}

        for x in range(3):
            key_name = 'key.%d' % x
            keys[key_name] = {'category': 'cat.%d' % x}

            description = 'description %s' % key_name
            value = 'value %s' % key_name
            default_values[key_name] = {
                'value': value, 'description': description
            }

        Key.insert_keys(self.db, keys, default_values)

        loaded_keys = self.db.query(Key).all()

        expect(loaded_keys).to_length(3)

        for key in loaded_keys:
            expect(keys).to_include(key.name)
            expect(key.to_dict()).to_equal(keys[key.name]['key'].to_dict())
            expect(key.category.name).to_be_like(keys[key.name]['category'])
            expect(keys[key.name]['default_value_description']).to_equal(
                'description %s' % key.name
            )
            expect(keys[key.name]['default_value']).to_equal(
                'value %s' % key.name
            )

    def test_can_update_keys(self):
        default_values = {'some.random.key': {
            'value': 100, 'description': 'my description'}
        }

        # Insert key and category

        keys = {'some.random.key': {'category': 'SEO'}}

        Key.insert_keys(self.db, keys, default_values)

        loaded_key = self.db.query(Key).one()

        expect(keys).to_include(loaded_key.name)
        expect(loaded_key.name).to_equal('some.random.key')
        expect(loaded_key.category.name).to_equal('SEO')

        # Update category

        keys = {'some.random.key': {'category': 'HTTP'}}

        Key.insert_keys(self.db, keys, default_values)

        loaded_key = self.db.query(Key).one()

        expect(keys).to_include(loaded_key.name)
        expect(loaded_key.name).to_equal('some.random.key')
        expect(loaded_key.category.name).to_equal('HTTP')

    def test_can_convert_key_to_dict(self):
        key = KeyFactory.create()

        key_dict = key.to_dict()

        expect(key_dict).to_be_like({
            'name': str(key.name),
            'category': str(key.category.name)
        })
