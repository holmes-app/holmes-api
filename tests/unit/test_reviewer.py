#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from ujson import dumps

import requests
from preggy import expect
from mock import patch, Mock

from holmes.reviewer import Reviewer, ReviewDAO
from holmes.config import Config
from holmes.validators.base import Validator
from tests.unit.base import ApiTestCase


class TestReviewDAO(ApiTestCase):
    def test_can_create_dao(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        expect(item.page_uuid).to_equal("uuid")
        expect(item.page_url).to_equal("http://www.globo.com")
        expect(item.facts).to_be_empty()
        expect(item.violations).to_be_empty()

    def test_can_add_fact(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        item.add_fact('some.fact', 'Some Title', 'value', 'unit')

        expect(item.facts).to_length(1)
        expect(item.facts['some.fact']).to_be_like({
            'key': 'some.fact',
            'title': 'Some Title',
            'value': 'value',
            'unit': 'unit'
        })

    def test_can_add_violation(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        item.add_violation('some.violation', 'Some Violation', 'Violation Description', 200)

        expect(item.violations).to_length(1)
        expect(item.violations[0]).to_be_like({
            'key': 'some.violation',
            'title': 'Some Violation',
            'description': 'Violation Description',
            'points': 200
        })


class TestReview(ApiTestCase):
    def get_reviewer(
            self, api_url=None, page_uuid=None, page_url='http://page.url',
            config=None, validators=[Validator]):

        if api_url is None:
            api_url = self.get_url('/')

        if page_uuid is None:
            page_uuid = uuid4()

        if config is None:
            config = Config()

        return Reviewer(
            api_url=api_url,
            page_uuid=page_uuid,
            page_url=page_url,
            config=config,
            validators=validators
        )

    def test_can_create_reviewer(self):
        page_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=page_uuid, config=config, validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_can_create_reviewer_with_page_string_uuid(self):
        page_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=page_uuid,
                                     config=config,
                                     validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_can_create_reviewer_with_review_string_uuid(self):
        page_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=page_uuid,
                                     config=config,
                                     validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_reviewer_fails_if_wrong_config(self):
        try:
            self.get_reviewer(config='wrong config object')
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('config argument must be an instance of holmes.config.Config')
        else:
            assert False, 'Should not have gotten this far'

    def test_reviewer_fails_if_wrong_validators(self):
        validators = [Validator, "wtf"]
        validators2 = [Validator, Config]

        try:
            self.get_reviewer(validators=validators)
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('All validators must subclass holmes.validators.base.Validator (Error: str)')
        else:
            assert False, 'Should not have gotten this far'

        try:
            self.get_reviewer(validators=validators2)
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('All validators must subclass holmes.validators.base.Validator (Error: type)')
        else:
            assert False, 'Should not have gotten this far'

    @patch.object(Reviewer, '_async_get')
    def test_load_content_call_async_get(self, get_mock):
        page_url = 'http://page.url'
        reviewer = self.get_reviewer()

        reviewer.responses[page_url] = {
            'status': 500,
            'content': '',
            'html': None
        }

        mock_callback = Mock()

        reviewer.load_content(mock_callback)
        get_mock.assert_called_once_with(page_url, mock_callback)

    def test_review_calls_validators(self):
        test_class = {}

        class MockValidator(Validator):
            def validate(self):
                test_class['has_validated'] = True

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url, validators=[MockValidator])

        reviewer.responses[page_url] = {
            'status': 200,
            'content': '<html><head></head><body></body></html>',
            'html': None
        }

        reviewer._wait_timeout = 1
        reviewer._wait_for_async_requests = Mock()

        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            reviewer.review()
            reviewer.run_validators()

        reviewer._wait_for_async_requests.assert_called_once_with(1)
        expect(test_class['has_validated']).to_be_true()

    @patch.object(ReviewDAO, 'add_fact')
    def test_reviewer_add_fact(self, fact_dao):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=400, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid)

            reviewer.add_fact('key', 'value', 'title', 'unit')
            fact_dao.assert_called_once_with('key', 'title', 'value', 'unit')

    @patch.object(ReviewDAO, 'add_violation')
    def test_reviewer_add_violation(self, violation_mock):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid)

            reviewer.add_violation('key', 'title', 'description', 100)

            violation_mock.assert_called_once_with('key', 'title', 'description', 100)

    def test_can_get_current(self):
        reviewer = self.get_reviewer()
        reviewer._current = 'test'

        response = reviewer.current
        expect(response).not_to_be_null()
        expect(response).to_equal('test')

    def test_enqueue_when_none(self):
        reviewer = self.get_reviewer()
        enqueue = reviewer.enqueue()
        expect(enqueue).to_be_null()

    @patch('requests.post')
    def test_can_enqueue_one_url(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='OK')
        reviewer = self.get_reviewer()
        reviewer.enqueue('http://globo.com')
        mock_post.assert_called_once_with(
            '%spage' % reviewer.api_url,
            data=dumps({
                'url': 'http://globo.com',
                'origin_uuid': str(reviewer.page_uuid)
            })
        )

    @patch('requests.post')
    def test_can_enqueue_multiple_urls(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='OK')
        reviewer = self.get_reviewer()
        reviewer.enqueue('http://globo.com', 'http://g1.globo.com')
        mock_post.assert_called_once_with(
            '%spages' % reviewer.api_url,
            data={'url': ('http://globo.com', 'http://g1.globo.com'),
                  'origin_uuid': str(reviewer.page_uuid)}
            )

    @patch('requests.post')
    @patch('logging.error')
    def test_enqueue_404(self, error_mock, mock_post):
        mock_post.return_value = Mock(status_code=404, text='Not Found')
        reviewer = self.get_reviewer()
        reviewer.enqueue('http://globo.com')
        error_mock.assert_called_once_with(
            "Could not enqueue page 'http://globo.com'! Status Code: 404, Error: Not Found"
        )

    def test_is_root(self):
        reviewer = self.get_reviewer(page_url="http://g1.globo.com")
        expect(reviewer.is_root()).to_equal(True)

        reviewer = self.get_reviewer(page_url="http://g1.globo.com/")
        expect(reviewer.is_root()).to_equal(True)

        reviewer = self.get_reviewer(page_url="http://g1.globo.com/index.html")
        expect(reviewer.is_root()).to_equal(False)
