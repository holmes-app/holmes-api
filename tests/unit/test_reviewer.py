#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from ujson import dumps

import requests
from preggy import expect
from mock import patch, Mock, call

from holmes.reviewer import Reviewer, ReviewDAO
from holmes.models import Page, Domain, Key, DomainsViolationsPrefs, Request
from holmes.config import Config
from holmes.validators.base import Validator
from tests.unit.base import ApiTestCase
from tests.fixtures import (
    DomainFactory, PageFactory, DomainsViolationsPrefsFactory
)


class TestReviewDAO(ApiTestCase):
    def test_can_create_dao(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        expect(item.page_uuid).to_equal("uuid")
        expect(item.page_url).to_equal("http://www.globo.com")
        expect(item.facts).to_be_empty()
        expect(item.violations).to_be_empty()

    def test_can_add_fact(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        item.add_fact('some.fact', 'value')

        expect(item.facts).to_length(1)
        expect(item.facts['some.fact']).to_be_like({
            'key': 'some.fact',
            'value': 'value',
        })

    def test_can_add_violation(self):
        item = ReviewDAO("uuid", "http://www.globo.com")

        item.add_violation('some.violation', 'value', 200)

        expect(item.violations).to_length(1)
        expect(item.violations[0]).to_be_like({
            'key': 'some.violation',
            'value': 'value',
            'points': 200
        })


class TestReview(ApiTestCase):
    @property
    def sync_cache(self):
        return self.connect_to_sync_redis()

    def get_reviewer(
            self, api_url=None, page_uuid=None, page_url='http://page.url',
            page_score=0.0, config=None, validators=[Validator], cache=None,
            db=None):

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
            page_score=page_score,
            config=config,
            validators=validators,
            cache=cache,
            db=db
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

            reviewer.add_fact('key', 'value')
            fact_dao.assert_called_once_with('key', 'value')

    @patch.object(ReviewDAO, 'add_violation')
    def test_reviewer_add_violation(self, violation_mock):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid)

            reviewer.add_violation('key', 'description', 100)

            violation_mock.assert_called_once_with('key', 'description', 100)

    def test_can_get_current(self):
        reviewer = self.get_reviewer()
        reviewer._current = 'test'

        response = reviewer.current
        expect(response).not_to_be_null()
        expect(response).to_equal('test')

    @patch.object(Page, 'add_page')
    def test_enqueue(self, add_page_mock):
        reviewer = self.get_reviewer()
        reviewer._wait_timeout = 1
        reviewer._wait_for_async_requests = Mock()
        reviewer.async_get_func = Mock()
        reviewer.girl = Mock()
        reviewer.db = None

        reviewer.enqueue([('http://www.ga.com/', 359.0)])

        add_page_mock.assert_has_calls(call(
            None,
            None,
            'http://www.ga.com/',
            359.0,
            reviewer.async_get_func,
            None,
            reviewer.config,
            reviewer.girl,
            reviewer.violation_definitions,
            reviewer.handle_page_added
        ))

        reviewer._wait_for_async_requests.assert_called_once_with(1)

    def test_enqueue_when_none(self):
        reviewer = self.get_reviewer()
        enqueue = reviewer.enqueue([])
        expect(enqueue).to_be_null()

    def test_is_root(self):
        reviewer = self.get_reviewer(page_url="http://g1.globo.com")
        expect(reviewer.is_root()).to_equal(True)

        reviewer = self.get_reviewer(page_url="http://g1.globo.com/")
        expect(reviewer.is_root()).to_equal(True)

        reviewer = self.get_reviewer(page_url="http://g1.globo.com/index.html")
        expect(reviewer.is_root()).to_equal(False)

    def test_can_get_domains_violations_prefs_by_key(self):
        self.db.query(DomainsViolationsPrefs).delete()
        self.db.query(Page).delete()
        self.db.query(Domain).delete()
        self.db.query(Key).delete()

        domain = DomainFactory.create(name='t.com')
        page = PageFactory.create(domain=domain, url='http://t.com/a.html')

        prefs = DomainsViolationsPrefsFactory.create(
            domain=domain,
            key=Key(name='page.title.size'),
            value='70'
        )

        reviewer = self.get_reviewer(
            page_uuid=page.uuid,
            page_url=page.url,
            cache=self.sync_cache
        )

        # Get default value

        reviewer.violation_definitions = None

        self.sync_cache.redis.delete('violations-prefs-%s' % domain.name)
        prefs = reviewer.get_domains_violations_prefs_by_key(None)
        expect(prefs).to_be_null()

        prefs = reviewer.get_domains_violations_prefs_by_key('my-key')
        expect(prefs).to_be_null()

        reviewer.violation_definitions = {
            'page.title.size': {'default_value': '70'},
        }

        self.sync_cache.redis.delete('violations-prefs-%s' % domain.name)
        prefs = reviewer.get_domains_violations_prefs_by_key('my-key')
        expect(prefs).to_be_null()

        self.sync_cache.redis.delete('violations-prefs-%s' % domain.name)
        prefs = reviewer.get_domains_violations_prefs_by_key('page.title.size')
        expect(prefs).to_equal('70')

        # Get configured value

        data = [{'key': 'page.title.size', 'value': '10'}]
        DomainsViolationsPrefs.update_by_domain(self.db, self.sync_cache, domain, data)
        prefs = reviewer.get_domains_violations_prefs_by_key('page.title.size')
        expect(prefs).to_equal('10')

    def test_cannot_save_request_for_external_domain(self):
        self.db.query(Request).delete()

        page_uuid = uuid4()

        reviewer = self.get_reviewer(page_uuid=page_uuid, db=self.db)

        url = 'http://google.com/robots.txt'
        response_mock = Mock(
            status_code=200,
            text='OK',
            request_time=0.1,
            effective_url=url
        )

        reviewer.publish = Mock()

        self.db.query(Domain).delete()

        reviewer.save_request(url, response_mock)

        req = self.db.query(Request).all()

        expect(req).to_length(0)
        expect(reviewer.publish.called).to_be_false()

    def test_can_save_request(self):
        self.db.query(Request).delete()

        domain = DomainFactory.create(name='t.com')
        page = PageFactory.create(domain=domain, url='http://t.com/a.html')

        reviewer = self.get_reviewer(
            page_uuid=page.uuid, page_url=page.url, db=self.db
        )

        url = 'http://t.com/robots.txt'
        response_mock = Mock(
            status_code=200,
            text='OK',
            request_time=0.1,
            effective_url=url
        )

        reviewer.publish = Mock()

        reviewer.save_request(url, response_mock)

        req = self.db.query(Request).all()

        expect(req).to_length(1)
        expect(req[0].url).to_equal(url)
        expect(req[0].status_code).to_equal(200)
        expect(req[0].response_time).to_equal(0.1)
        expect(req[0].domain_name).to_equal('t.com')
        expect(req[0].review_url).to_equal('http://t.com/a.html')

        expect(reviewer.publish.called).to_be_true()

        reviewer.publish.assert_called_once_with(
            dumps({'url': url, 'type': 'new-request'})
        )
