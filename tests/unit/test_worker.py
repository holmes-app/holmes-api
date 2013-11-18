#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join
from uuid import uuid4

from preggy import expect
from mock import patch, Mock
from octopus import Octopus

import holmes.worker
from holmes import __version__
from holmes.worker import HolmesWorker
from holmes.config import Config
from holmes.reviewer import InvalidReviewError
from tests.unit.base import ApiTestCase


class MockResponse(object):
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text


class WorkerTestCase(ApiTestCase):
    root_path = abspath(join(dirname(__file__), '..', '..'))

    def test_initialize(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        expect(worker.uuid).to_be_null()
        expect(worker.working).to_be_true()

        expect(worker.facters).to_length(1)
        expect(worker.validators).to_length(1)

        expect(worker.otto).to_be_instance_of(Octopus)

    def test_config_parser(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        parser_mock = Mock()

        worker.config_parser(parser_mock)

        parser_mock.add_argument.assert_called_once_with(
            '--concurrency',
            '-t',
            type=int,
            help='Number of threads to use for Octopus (doing GETs concurrently)'
        )

    def test_proxies_property(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expect(worker.proxies).to_be_like({
            'http': 'proxy:8080',
            'https': 'proxy:8080'
        })

    def test_async_get(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        otto_mock = Mock()
        worker.otto = otto_mock

        worker.async_get("url", "handler", 'GET', test="test")
        otto_mock.enqueue.assert_called_once_with('url', 'handler', 'GET', test='test', proxies={'http': 'proxy:8080', 'https': 'proxy:8080'})

    @patch.object(holmes.worker.requests, 'get')
    def test_get(self, get_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        worker.get('url')

        get_mock.assert_called_once_with('http://localhost:2368/url', proxies={'http': 'proxy:8080', 'https': 'proxy:8080'})

    @patch.object(holmes.worker.requests, 'post')
    def test_post(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        worker.post('url', data={'test': 'test'})

        post_mock.assert_called_once_with(
            'http://localhost:2368/url',
            data={'test': 'test'},
            proxies={'http': 'proxy:8080', 'https': 'proxy:8080'})

    def test_description(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expected = "holmes-worker (holmes-api v%s)" % (
            __version__
        )

        expect(worker.get_description()).to_be_like(expected)

    def test_config_class(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expect(worker.get_config_class()).to_equal(Config)

    @patch.object(holmes.worker.requests, 'post')
    def test_stop_work(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()

        worker.stop_work()

        post_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/dead' % str(worker.uuid),
            proxies={'http': 'proxy:8080', 'https': 'proxy:8080'},
            data={'worker_uuid': worker.uuid}
        )

    @patch.object(HolmesWorker, '_ping_api')
    def test_do_work_works_even_if_api_is_down(self, ping_api_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        ping_api_mock.return_value = False

        worker.do_work()

        expect(worker.uuid).not_to_be_null()

    @patch.object(HolmesWorker, '_start_job')
    @patch.object(HolmesWorker, '_load_next_job')
    @patch.object(HolmesWorker, '_ping_api')
    def test_do_work_if_api_is_up_but_no_job_to_do(self, ping_api_mock, load_next_job_mock, start_job_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        ping_api_mock.return_value = True
        load_next_job_mock.return_value = None

        worker.do_work()

        expect(worker.uuid).not_to_be_null()
        start_job_mock.assert_has_calls([])

    @patch.object(HolmesWorker, '_start_reviewer')
    @patch.object(HolmesWorker, '_start_job')
    @patch.object(HolmesWorker, '_load_next_job')
    @patch.object(HolmesWorker, '_ping_api')
    def test_do_work_if_api_is_up_and_job_available(
        self,
        ping_api_mock,
        load_next_job_mock,
        start_job_mock,
        start_reviewer_mock
    ):

        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        job = {
            'url': 'some-url',
            'page': 'some-uuid'
        }

        ping_api_mock.return_value = True
        load_next_job_mock.return_value = job

        worker.do_work()

        expect(worker.uuid).not_to_be_null()

        start_job_mock.assert_called_once_with(
            'some-url'
        )

        start_reviewer_mock.assert_called_once_with(
            job=job
        )

    @patch.object(HolmesWorker, '_start_reviewer')
    @patch.object(HolmesWorker, '_start_job')
    @patch.object(HolmesWorker, '_load_next_job')
    @patch.object(HolmesWorker, '_ping_api')
    @patch.object(holmes.worker, 'logging')
    def test_do_work_if_api_is_up_and_job_available_but_reviewer_fails(
        self,
        logging_mock,
        ping_api_mock,
        load_next_job_mock,
        start_job_mock,
        start_reviewer_mock
    ):

        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        job = {
            'url': 'some-url',
            'page': 'some-uuid'
        }

        ping_api_mock.return_value = True
        load_next_job_mock.return_value = job
        start_reviewer_mock.side_effect = InvalidReviewError()

        worker.do_work()

        expect(worker.uuid).not_to_be_null()

        start_job_mock.assert_called_once_with(
            'some-url'
        )

        logging_mock.error.assert_called_once_with('Fail to review some-url: ')


#class WorkerTestCase(ApiTestCase):
    #root_path = abspath(join(dirname(__file__), '..', '..'))

    #def get_worker(self):
        #worker = holmes.worker.HolmesWorker([])
        #worker.config = Config(**self.get_config())
        #return worker

    #def get_config(self):
        #cfg = super(WorkerTestCase, self).get_config()
        #cfg['WORKER_SLEEP_TIME'] = 1
        #cfg['HOLMES_API_URL'] = 'http://localhost:2368'
        #cfg['VALIDATORS'] = [
            #'holmes.validators.js_requests.JSRequestsValidator',
            #'holmes.validators.total_requests.TotalRequestsValidator',
        #]

        #return cfg

    #@patch('requests.post')
    #def test_worker_working_flag(self, requests_mock):
        #worker = self.get_worker()

        #expect(worker.working).to_be_true()
        #worker.stop_work()
        #expect(worker.working).to_be_false()

        #expect(requests_mock.called).to_be_true()
        #requests_mock.assert_called_once_with(
            #'http://localhost:2368/worker/%s/dead' % worker.uuid,
            #proxies=None,
            #data={'worker_uuid': worker.uuid}
        #)

    #def test_worker_can_create_an_instance(self):
        #worker = holmes.worker.HolmesWorker([])
        #expect(worker.working).to_be_true()

    #def test_worker_do_work(self):
        #worker = self.get_worker()

        #worker._ping_api = Mock()
        #job = {'page': self.ZERO_UUID, 'review': self.ZERO_UUID, 'url': 'http://globo.com'}
        #worker._load_next_job = Mock(return_value=job)
        #worker._start_job = Mock()
        #worker._start_reviewer = Mock()
        #worker._complete_job = Mock()

        #worker.do_work()

        #expect(worker._ping_api.called).to_be_true()
        #expect(worker._load_next_job.called).to_be_true()
        #expect(worker._start_job.called).to_be_true()
        #worker._start_job.assert_called_once_with(self.ZERO_UUID)
        #worker._start_reviewer.assert_called_once_with(job=job)
        #worker._complete_job.assert_called_once_with(self.ZERO_UUID, error=None)

    #@patch.object(holmes.worker.HolmesWorker, '_ping_api')
    #def test_worker_do_work_calling_ping_api(self, ping_api_mock):
        #worker = holmes.worker.HolmesWorker([])
        #worker._load_next_job = Mock(return_value=None)
        #worker.do_work()
        #expect(ping_api_mock.called).to_be_true()

    #@patch('requests.post')
    #def test_worker_ping_api(self, requests_mock):
        #worker = self.get_worker()
        #worker._ping_api()
        #expect(requests_mock.called).to_be_true()
        #requests_mock.assert_called_once_with(
            #'http://localhost:2368/worker/%s/alive' % worker.uuid,
            #data={'worker_uuid': worker.uuid},
            #proxies=None
        #)

    #@patch('requests.post')
    #def test_worker_ping_api_connection_error(self, ping_api_mock):
        #ping_api_mock.side_effect = ConnectionError()
        #worker = self.get_worker()
        #worker.do_work()
        #expect(worker.working).to_be_false()

    #@patch('requests.post')
    #def test_worker_load_next_job_error(self, load_next_job_mock):
        #load_next_job_mock.side_effect = ConnectionError()
        #worker = self.get_worker()
        #worker._load_next_job()
        #expect(worker.working).to_be_false()

    #@patch('requests.post')
    #def test_worker_load_next_job_must_call_api(self, load_next_job_mock):
        #response = MockResponse(200, '')
        #load_next_job_mock.return_value = response
        #worker = self.get_worker()
        #worker._load_next_job()

        #expect(load_next_job_mock.called).to_be_true()
        #load_next_job_mock.assert_called_once_with(
            #'http://localhost:2368/next',
            #data={},
            #proxies=None)

    #@patch('requests.post')
    #def test_worker_load_next_job_without_jobs(self, load_next_job_mock):
        #response = MockResponse(200, '')
        #load_next_job_mock.return_value = response
        #worker = self.get_worker()
        #next_job = worker._load_next_job()

        #expect(next_job).to_be_null()

    #@gen_test
    #def test_worker_load_next_job(self):
        #review = ReviewFactory.create()

        #expected = '{"page": "%s", "review": "%s", "url": "%s"}' % (
            #str(review.page.uuid),
            #str(review.uuid),
            #review.page.url
        #)

        #response = MockResponse(200, expected)

        #requests.post = Mock(return_value=response)

        #worker = holmes.worker.HolmesWorker([])
        #next_job = worker._load_next_job()

        #expect(next_job).not_to_be_null()
        #expect(next_job['page']).to_equal(str(review.page.uuid))
        #expect(next_job['review']).to_equal(str(review.uuid))
        #expect(next_job['url']).to_equal(str(review.page.url))

    #@patch('requests.post')
    #def test_worker_start_error(self, load_start_job_mock):
        #load_start_job_mock.side_effect = ConnectionError()
        #worker = self.get_worker()
        #worker._start_job(self.ZERO_UUID)
        #expect(worker.working).to_be_true()

    #@patch('requests.post')
    #def test_worker_start_call_api(self, requests_mock):
        #response = MockResponse(200, 'OK')
        #requests_mock.return_value = response
        #worker = self.get_worker()
        #result = worker._start_job(self.ZERO_UUID)
        #expect(requests_mock.called).to_be_true()
        #requests_mock.assert_called_once_with(
            #'http://localhost:2368/worker/%s/review/%s/start' % (str(worker.uuid), self.ZERO_UUID),
            #proxies=None,
            #data={}
        #)
        #expect(result).to_be_true()

    #@patch('requests.post')
    #def test_worker_start_null_job(self, requests_mock):
        #response = MockResponse(200, 'OK')
        #requests_mock.return_value = response
        #worker = self.get_worker()
        #result = worker._start_job(None)
        #expect(requests_mock.called).to_be_false()
        #expect(result).to_be_false()

    #@patch('requests.post')
    #def test_worker_complete_error(self, load_start_job_mock):
        #load_start_job_mock.side_effect = ConnectionError()
        #worker = self.get_worker()
        #worker._complete_job(self.ZERO_UUID)
        #expect(worker.working).to_be_true()

    #@patch('requests.post')
    #def test_worker_complete_call_api(self, requests_mock):
        #response = MockResponse(200, 'OK')
        #requests_mock.return_value = response
        #worker = self.get_worker()
        #worker._complete_job(self.ZERO_UUID)
        #requests_mock.assert_called_once_with(
            #'http://localhost:2368/worker/%s/review/%s/complete' % (str(worker.uuid), self.ZERO_UUID),
            #data='{"error":null}',
            #proxies=None)

    #@patch('requests.post')
    #def test_worker_complete_null_job(self, requests_mock):
        #response = MockResponse(200, 'OK')
        #requests_mock.return_value = response
        #worker = self.get_worker()
        #result = worker._complete_job(None)
        #expect(requests_mock.called).to_be_false()
        #expect(result).to_be_false()

    #def test_do_work_without_next_job(self):
        #worker = self.get_worker()

        #job = None
        #worker._load_next_job = Mock(return_value=job)
        #worker._ping_api = Mock(return_value=True)
        #worker._start_job = Mock()
        #worker._complete_job = Mock()

        #worker.do_work()

        #expect(worker._start_job.called).to_be_false()
        #expect(worker._complete_job.called).to_be_false()

    #@gen_test
    #def test_do_work_with_next_job(self):
        #review = ReviewFactory.create()

        #worker = self.get_worker()

        #job = {'page': str(review.page.uuid), 'review': str(review.uuid), 'url': review.page.url}
        #worker._load_next_job = Mock(return_value=job)
        #worker._ping_api = Mock(return_value=True)
        #worker._start_job = Mock()
        #worker._start_reviewer = Mock()
        #worker._complete_job = Mock()

        #worker.do_work()

        #expect(worker._start_job.called).to_be_true()
        #expect(worker._complete_job.called).to_be_true()

    #@gen_test
    #def test_do_work_invalid_review_error(self):
        #review = ReviewFactory.create()

        #worker = self.get_worker()

        #job = {'page': str(review.page.uuid), 'review': str(review.uuid), 'url': review.page.url}
        #worker._load_next_job = Mock(return_value=job)
        #worker._ping_api = Mock(return_value=True)
        #worker._start_job = Mock()
        #worker._start_reviewer = Mock(side_effect=InvalidReviewError)
        #worker._complete_job = Mock()

        #worker.do_work()

        #expect(worker._start_job.called).to_be_true()
        #expect(worker._complete_job.called).to_be_true()

    #def test_load_validators_none(self):
        #worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/unit/config/test_empty_conf.conf')])
        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(0)

    #def test_load_validators(self):
        #worker = self.get_worker()

        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(2)

        #for validator in validators:
            #try:
                #expect(issubclass(validator, Validator)).to_be_true()
            #except TypeError:
                #assert False, 'Expect all validators to be subclass of holmes.validators.base.Validator'

    #def test_load_validators_can_instantiate_a_validator(self):
        #worker = self.get_worker()
        #worker.config.VALIDATORS = ['holmes.validators.js_requests.JSRequestsValidator']

        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(1)

        #validator_class = validators[0]
        #validator = validator_class(None)
        #expect(type(validator)).to_equal(holmes.validators.js_requests.JSRequestsValidator)

    #def test_load_validators_invalid_validator_full_name(self):
        #worker = self.get_worker()
        #worker.config.VALIDATORS += ['JSRequestsValidator']

        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(2)

    #def test_load_validators_unknown_class(self):
        #worker = self.get_worker()
        #worker.config.VALIDATORS += ['holmes.validators.js_requests.ValidatorDoesNotExist']

        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(2)

    #def test_load_validators_unknown_module(self):
        #worker = self.get_worker()
        #worker.config.VALIDATORS += ['holmes.validators.unknown_module.ValidatorDoesNotExist']

        #validators = worker._load_validators()

        #expect(validators).not_to_be_null()
        #expect(validators).to_length(2)

    #@patch("holmes.reviewer.Reviewer.review")
    #def test_start_reviwer_without_job(self, mock_reviewer):
        #worker = self.get_worker()
        #worker._start_reviewer(None)
        #expect(mock_reviewer.called).not_to_be_true()

    #@patch("holmes.reviewer.Reviewer.review")
    #def test_start_reviwer(self, mock_reviewer):
        #worker = self.get_worker()
        #worker._load_validators = Mock(return_value=[])
        #job = {'page': self.ZERO_UUID, 'review': self.ZERO_UUID, 'url': 'http://globo.com'}
        #worker._start_reviewer(job=job)
        #expect(mock_reviewer.called).to_be_true()
