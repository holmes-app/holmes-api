#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.base import Validator
from tests.fixtures import PageFactory, ReviewFactory
from tests.unit.base import ApiTestCase


class TestBaseValidator(ApiTestCase, unittest.TestCase):
    @property
    def sync_cache(self):
        return self.connect_to_sync_redis()

    def test_can_validate(self):
        expect(Validator(None).validate()).to_be_true()

    def test_can_add_fact(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).add_fact('test', 10)
        mock_reviewer.add_fact.assert_called_once_with('test', 10)

    def test_can_add_violation(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).add_violation('test', 'value', 100)
        mock_reviewer.add_violation.assert_called_once_with('test', 'value', 100)

    def test_can_return_reviewer_info(self):
        review = ReviewFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=review.page.uuid,
            page_url=review.page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = Validator(reviewer)

        expect(validator.page_uuid).to_equal(review.page.uuid)
        expect(validator.page_url).to_equal(review.page.url)
        expect(validator.config).to_equal(reviewer.config)

    def test_is_absolute(self):
        validator = Validator(None)
        expect(validator.is_absolute('http://globoi.com/index.html')).to_be_true()

    def test_is_relative(self):
        validator = Validator(None)
        expect(validator.is_absolute('/index.html')).to_be_false()

    def test_can_rebase(self):
        page = PageFactory.create(url='http://globoi.com/test/index.html')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = Validator(reviewer)

        expect(validator.rebase('index.png')).to_equal('http://globoi.com/test/index.png')
        expect(validator.rebase('/index.png')).to_equal('http://globoi.com/index.png')

    def test_will_call_reviewer_enqueue(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        reviewer.enqueue = Mock()

        validator = Validator(reviewer)
        validator.enqueue('/')

        reviewer.enqueue.assert_called_once_with('/')

    def test_will_call_reviewer_add_fact(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        reviewer.add_fact = Mock()

        validator = Validator(reviewer)
        validator.add_fact('random.fact', 'value')
        reviewer.add_fact.assert_called_once_with('random.fact', 'value')

    def test_will_call_reviewer_add_violation(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        reviewer.add_violation = Mock()

        validator = Validator(reviewer)
        validator.add_violation('random.violation', 'random', 0)
        reviewer.add_violation.assert_called_once_with('random.violation', 'random', 0)

    def test_can_encode_content(self):
        validator = Validator(None)
        content = u'random content'
        gziped_content = validator.to_gzip(content)

        expect(content).to_equal(gziped_content.decode('zip'))

    def test_test_url_method(self):
        validator = Validator(None)

        expect(validator.test_url('the-url', Mock(status_code=200, url='the-url'))).to_equal(True)
        expect(validator.test_url('the-url', Mock(status_code=404))).to_equal(False)
        expect(validator.test_url('the-url', Mock(status_code=302))).to_equal(False)
        expect(validator.test_url('the-url', Mock(status_code=307))).to_equal(False)
        expect(validator.test_url('the-url-root', Mock(status_code=200, url='the-url-index'))).to_equal(False)

        callback_1 = Mock()
        callback_2 = Mock()
        expect(validator.test_url('the-url', Mock(status_code=404), callback_1, callback_2)).to_equal(False)
        expect(callback_1.call_count).to_equal(1)
        expect(callback_2.call_count).to_equal(0)

        callback_1 = Mock()
        callback_2 = Mock()
        expect(validator.test_url('the-url', Mock(status_code=302), callback_1, callback_2)).to_equal(False)
        expect(callback_1.call_count).to_equal(0)
        expect(callback_2.call_count).to_equal(1)

        callback_1 = Mock()
        callback_2 = Mock()
        expect(validator.test_url('the-url', Mock(status_code=307), callback_1, callback_2)).to_equal(False)
        expect(callback_1.call_count).to_equal(0)
        expect(callback_2.call_count).to_equal(1)

    def test_send_url(self):
        validator = Validator(Mock(config=Mock(MAX_ENQUEUE_BUFFER_LENGTH=1)))

        validator.flush = Mock()
        validator.test_url = Mock(return_value=True)

        expect(len(validator.url_buffer)).to_equal(0)

        validator.send_url('the-url', 0.0, 'the-response')

        expect(len(validator.url_buffer)).to_equal(1)
        expect(validator.flush.call_count).to_equal(0)

        validator.send_url('the-url-2', 0.0, 'the-response-2')

        expect(len(validator.url_buffer)).to_equal(2)
        expect(validator.flush.call_count).to_equal(1)

    def test_flush_method(self):
        validator = Validator(None)
        validator.enqueue = Mock()

        validator.flush()

        expect(validator.enqueue.call_count).to_equal(0)

        validator = Validator(None)
        validator.url_buffer = [1, 2, 3]
        validator.enqueue = Mock()

        validator.flush()

        validator.enqueue.assert_called_once_with([1, 2, 3])

    def test_not_implemented_methods(self):
        validator = Validator(None)

        self.assertRaises(NotImplementedError, validator.broken_link_violation)
        self.assertRaises(NotImplementedError, validator.moved_link_violation)

    def test_normalize_url_with_valid_url(self):
        validator = Validator(None)
        url = validator.normalize_url('http://globo.com')

        expect(url).to_equal('http://globo.com')

    def test_normalize_url_with_invalid_url(self):
        validator = Validator(None)
        url = validator.normalize_url('http://]globo.com')

        expect(url).to_be_null()

    def test_normalize_url_with_not_absoulte_url(self):
        page = PageFactory.create(url='http://globoi.com/test/index.html')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = Validator(reviewer)

        url = validator.normalize_url('/metal.html')

        expect(url).to_equal('http://globoi.com/metal.html')

    def test_can_get_default_violations_values(self):
        config = Config()

        validator = Validator(None)

        values = validator.get_default_violations_values(config)

        expect(values).to_equal({})

    def test_can_get_violation_pref(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'page.title.size': {'default_value': 70},
        }

        validator = Validator(reviewer)

        page_title_size = validator.get_violation_pref('page.title.size')

        expect(page_title_size).to_equal(70)
