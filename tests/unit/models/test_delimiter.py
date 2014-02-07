#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
from preggy import expect

from holmes.models import Delimiter
from tests.unit.base import ApiTestCase
from tests.fixtures import DelimiterFactory


class TestUser(ApiTestCase):

    def test_can_create_delimiter(self):
        delimiter = DelimiterFactory.create(url='http://test.com/')

        expect(str(delimiter)).to_be_like('%s' % delimiter.url)

        expect(delimiter.id).not_to_be_null()
        expect(delimiter.url).to_equal('http://test.com/')
        expect(delimiter.value).to_equal(10)

    def test_can_convert_user_to_dict(self):
        delimiter = DelimiterFactory.create()

        delimiter_dict = delimiter.to_dict()

        expect(delimiter_dict['url']).to_equal(delimiter.url)
        expect(delimiter_dict['value']).to_equal(delimiter.value)

    def test_can_get_delimiter_by_url_hash(self):
        self.db.query(Delimiter).delete()

        delimiter = DelimiterFactory.create(url='http://test.com/')

        url_hash = hashlib.sha512('http://test.com/').hexdigest()

        loaded_delimiter = Delimiter.by_url_hash(url_hash, self.db)
        expect(loaded_delimiter.id).to_equal(delimiter.id)

        invalid_delimiter = Delimiter.by_url_hash('00000000', self.db)
        expect(invalid_delimiter).to_be_null()

    def test_can_get_delimiter_by_url(self):
        self.db.query(Delimiter).delete()

        delimiter = DelimiterFactory.create(url='http://test.com/')

        loaded_delimiter = Delimiter.by_url('http://test.com/', self.db)
        expect(loaded_delimiter.id).to_equal(delimiter.id)

        invalid_delimiter = Delimiter.by_url('http://test.com/1', self.db)
        expect(invalid_delimiter).to_be_null()

    def test_can_get_all_delimiters(self):
        self.db.query(Delimiter).delete()

        delimiter = DelimiterFactory.create(url='http://test.com/')
        DelimiterFactory.create()
        DelimiterFactory.create()

        delimiters = Delimiter.get_all(self.db)

        expect(delimiters).not_to_be_null()
        expect(delimiters).to_length(3)
        expect(delimiters).to_include(delimiter)

    def test_can_add_or_update_delimiter(self):
        self.db.query(Delimiter).delete()

        delimiters = Delimiter.get_all(self.db)
        expect(delimiters).to_equal([])

        # Add
        url = 'http://globo.com/'
        value = 2
        Delimiter.add_or_update_delimiter(self.db, url, value)
        delimiter = Delimiter.by_url(url, self.db)

        expect(delimiter.value).to_equal(2)

        # Update
        url = 'http://globo.com/'
        value = 3
        Delimiter.add_or_update_delimiter(self.db, url, value)
        delimiter = Delimiter.by_url(url, self.db)

        expect(delimiter.value).to_equal(3)
