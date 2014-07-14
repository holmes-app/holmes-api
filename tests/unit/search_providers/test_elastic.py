#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from mock import Mock, patch
from preggy import expect
from pyelasticsearch import InvalidJsonResponseError
from tornado.concurrent import Future
from tornado.testing import gen_test

from holmes.search_providers.elastic import ElasticSearchProvider

from tests.unit.base import ApiTestCase
from tests.fixtures import ReviewFactory, PageFactory, DomainFactory


class TestElasticSearchProvider(ApiTestCase):

    def setUp(self):
        super(TestElasticSearchProvider, self).setUp()
        self.config = self.server.config
        self.index = self.config.get('ELASTIC_SEARCH_INDEX')
        self.ES = ElasticSearchProvider(self.config, self.db)
        self.ES.activate_debug()

    def mkfuture(self, result):
        future = Future()
        future.set_result(result)
        return future

    @patch('sqlalchemy.create_engine')
    @patch('sqlalchemy.orm.scoped_session')
    @patch('sqlalchemy.orm.sessionmaker')
    def test_can_connect_to_db(self, sessionmaker_mock, scoped_session_mock, create_engine_mock):
        self.ES.connect_to_db()

        expect(create_engine_mock.call_count).to_equal(1)
        expect(self.ES.db).to_be_instance_of(Mock)
        create_engine_mock.assert_called_with(
            self.config.get('SQLALCHEMY_CONNECTION_STRING'),
            convert_unicode=True,
            pool_size=1,
            max_overflow=0,
            echo=self.ES.debug
        )

    def test_can_assemble_inner_query(self):
        expected = {
            'match_all': {}
        }

        query = self.ES._assemble_inner_query()

        expect(query).to_be_like(expected)

    def test_can_assemble_inner_query_with_args(self):
        expected = {
            'prefix': {
                'page_url': 'domain_url/page_filter'
            }
        }

        query = self.ES._assemble_inner_query(
            domain=Mock(url='domain_url'),
            page_filter='page_filter'
        )

        expect(query).to_be_like(expected)

    def test_can_assemble_outer_query(self):
        filter_terms = ['term1', 'term2']

        expected = {
            'filtered': {
                'query': 'inner_query',
                'filter': {
                    'and': [{
                        'term': filter_term
                    } for filter_term in filter_terms]
                }
            }
        }

        query = self.ES._assemble_outer_query('inner_query', filter_terms)

        expect(query).to_be_like(expected)

    def test_can_assemble_filter_terms(self):
        expected = [{'keys.id': 35}, {'domain_id': 359}]

        query = self.ES._assemble_filter_terms(35, Mock(id=359))

        expect(query).to_be_like(expected)

    def test_can_gen_doc(self):
        review = ReviewFactory.create(
            is_active=True,
            number_of_violations=6,
            created_date=datetime(2014, 04, 15, 11, 44),
            completed_date=datetime(2014, 04, 15, 11, 44),
        )

        expected = {
            'keys': [{'id': violation.key_id} for violation in review.violations],
            'uuid': str(review.uuid),
            'completed_date': review.completed_date,
            'violation_count': 6,
            'page_id': review.page_id,
            'page_uuid': str(review.page.uuid),
            'page_url': review.page.url,
            'page_last_review_date': review.page.last_review_date,
            'domain_id': review.domain_id,
            'domain_name': review.domain.name,
        }

        doc = self.ES.gen_doc(review)

        expect(doc).to_be_like(expected)

    @patch('logging.error')
    @patch('time.sleep')
    def test_can_index_review(self, logging_error_mock, time_sleep_mock):
        self.ES.gen_doc = Mock(return_value=0)
        self.ES.syncES = Mock(send_request=Mock())

        for i in range(6):
            review = Mock(page_id=0)

            self.ES.index_review(review)

        expect(self.ES.gen_doc.call_count).to_equal(6)
        expect(self.ES.syncES.send_request.call_count).to_equal(6)
        self.ES.syncES.send_request.assert_called_with(
            method='POST',
            path_components=[self.index, 'review', 0],
            body='0',
            encode_body=False
        )

        expect(logging_error_mock.called).to_be_false()
        expect(time_sleep_mock.called).to_be_false()

    @patch('logging.error')
    @patch('time.sleep')
    def test_try_index_review_up_to_three_times(self, logging_error_mock, time_sleep_mock):

        def exception_raiser(*args, **kwargs):
            raise InvalidJsonResponseError(
                'Invalid JSON returned from ES: <Response [504]>'
            )

        self.ES.gen_doc = Mock(return_value=0)
        self.ES.syncES = Mock(send_request=Mock(side_effect=exception_raiser))

        review = Mock(page_id=0)

        self.ES.index_review(review)

        expect(self.ES.gen_doc.call_count).to_equal(3)
        expect(self.ES.syncES.send_request.call_count).to_equal(3)
        self.ES.syncES.send_request.assert_called_with(
            method='POST',
            path_components=[self.index, 'review', 0],
            body='0',
            encode_body=False
        )

        expect(logging_error_mock.call_count).to_equal(3)
        expect(time_sleep_mock.call_count).to_equal(3)

    def test_can_index_reviews(self):
        expected_body = '{"index":{"_type":"review","_id":0}}\n{"page_id":0}\n' * 5

        self.ES.gen_doc = Mock(return_value={'page_id': 0})
        self.ES.syncES = Mock(send_request=Mock())

        pages = [Mock(last_review=0) for _ in range(100)]

        self.ES.index_reviews(pages, len(pages), 5)

        expect(self.ES.gen_doc.call_count).to_equal(100)
        expect(self.ES.syncES.send_request.call_count).to_equal(20)
        self.ES.syncES.send_request.assert_called_with(
            method='POST',
            path_components=[self.index, '_bulk'],
            body=expected_body,
            encode_body=False
        )

    @gen_test
    def test_can_get_by_violation_key_name(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(__getitem__=Mock())
        hits = 6 * [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(return_value='datetime')

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                response = yield self.ES.get_by_violation_key_name(
                    key_id=1,
                    current_page=1,
                    page_size=10,
                    callback=callback_mock
                )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(len(hits))
        expect(getitem_mock.__getitem__.call_count).to_equal(5 * len(hits))
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_by_violation_key_name_with_server_erroneous_response(self):

        def search_side_effect(*args, **kwargs):
            error_mock = Mock(
                error=Mock(message='error'),
                body='error'
            )
            kwargs['callback'](error_mock)

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        callback_mock = Mock(side_effect=self.stop)

        with patch('logging.error') as logging_error_mock:
            response = yield self.ES.get_by_violation_key_name(
                key_id=1,
                current_page=1,
                page_size=10,
                callback=callback_mock
            )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: erroneous response (error [error])')
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_by_violation_key_name_with_invalid_response(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        def exception_raiser(*args, **kwargs):
            raise KeyError(args[0])

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(
            __getitem__=Mock(side_effect=exception_raiser)
        )
        hits = [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(return_value='datetime')

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                with patch('logging.error') as logging_error_mock:
                    response = yield self.ES.get_by_violation_key_name(
                        key_id=1,
                        current_page=1,
                        page_size=10,
                        callback=callback_mock
                    )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(0)
        expect(getitem_mock.__getitem__.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: invalid response (<type \'exceptions.KeyError\'> [completed_date])')
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_by_violation_key_name_with_invalid_response_again(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        def exception_raiser(*args, **kwargs):
            raise TypeError('a float is required')

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(__getitem__=Mock())
        hits = [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(
            return_value='datetime',
            side_effect=exception_raiser
        )

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                with patch('logging.error') as logging_error_mock:
                    response = yield self.ES.get_by_violation_key_name(
                        key_id=1,
                        current_page=1,
                        page_size=10,
                        callback=callback_mock
                    )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(1)
        expect(getitem_mock.__getitem__.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: invalid response (<type \'exceptions.TypeError\'> [a float is required])')
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_domain_active_reviews(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(__getitem__=Mock(return_value=[]))
        hits = 6 * [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(return_value='datetime')

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                response = yield self.ES.get_domain_active_reviews(
                    domain=Mock(id=359),
                    current_page=1,
                    page_size=10,
                    callback=callback_mock
                )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(len(hits))
        expect(getitem_mock.__getitem__.call_count).to_equal(5 * len(hits))
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_domain_active_reviews_with_server_erroneous_response(self):

        def search_side_effect(*args, **kwargs):
            error_mock = Mock(
                error=Mock(message='error'),
                body='error'
            )
            kwargs['callback'](error_mock)

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        callback_mock = Mock(side_effect=self.stop)

        with patch('logging.error') as logging_error_mock:
            response = yield self.ES.get_domain_active_reviews(
                domain=Mock(id=359),
                current_page=1,
                page_size=10,
                callback=callback_mock
            )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: erroneous response (error [error])')
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_domain_active_reviews_with_invalid_response(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        def exception_raiser(*args, **kwargs):
            raise KeyError(args[0])

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(
            __getitem__=Mock(side_effect=exception_raiser)
        )
        hits = [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(return_value='datetime')

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                with patch('logging.error') as logging_error_mock:
                    response = yield self.ES.get_domain_active_reviews(
                        domain=Mock(id=359),
                        current_page=1,
                        page_size=10,
                        callback=callback_mock
                    )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(0)
        expect(getitem_mock.__getitem__.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: invalid response (<type \'exceptions.KeyError\'> [completed_date])')
        callback_mock.assert_called_once_with(response)

    @gen_test
    def test_can_get_domain_active_reviews_with_invalid_response_again(self):

        def search_side_effect(*args, **kwargs):
            kwargs['callback'](Mock(error=None))

        def exception_raiser(*args, **kwargs):
            raise TypeError('a float is required')

        self.ES.asyncES = Mock(
            search=Mock(side_effect=search_side_effect)
        )

        getitem_mock = Mock(__getitem__=Mock(return_value=[]))
        hits = [{'_source': getitem_mock}]
        fake_body = {'total': len(hits), 'hits': {'hits': hits}}

        utcfromtimestamp_mock = Mock(
            return_value='datetime',
            side_effect=exception_raiser
        )

        callback_mock = Mock(side_effect=self.stop)

        with patch('holmes.search_providers.elastic.loads', return_value=fake_body):
            with patch('holmes.search_providers.elastic.datetime', utcfromtimestamp=utcfromtimestamp_mock):
                with patch('logging.error') as logging_error_mock:
                    response = yield self.ES.get_domain_active_reviews(
                        domain=Mock(id=359),
                        current_page=1,
                        page_size=10,
                        callback=callback_mock
                    )

        expect(self.ES.asyncES.search.call_count).to_equal(1)
        expect(utcfromtimestamp_mock.call_count).to_equal(1)
        expect(getitem_mock.__getitem__.call_count).to_equal(1)
        logging_error_mock.assert_called_once_with('ElasticSearchProvider: invalid response (<type \'exceptions.TypeError\'> [a float is required])')
        callback_mock.assert_called_once_with(response)
