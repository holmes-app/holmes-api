#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join
from uuid import uuid4

from preggy import expect
from mock import patch, Mock, call
from octopus import TornadoOctopus
from requests.exceptions import ConnectionError

import holmes.worker
from holmes import __version__
from holmes.reviewer import InvalidReviewError
from holmes.worker import HolmesWorker
from holmes.config import Config
from tests.unit.base import ApiTestCase


class MockResponse(object):
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text


class WorkerTestCase(ApiTestCase):
    root_path = abspath(join(dirname(__file__), '..', '..'))

    @patch('uuid.UUID')
    def test_initialize(self, uuid):
        uuid.return_value = Mock(hex='my-uuid4')

        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        expect(worker.uuid).to_equal('my-uuid4')
        expect(worker.working).to_be_true()

        expect(worker.facters).to_length(1)
        expect(worker.validators).to_length(1)

        expect(worker.otto).to_be_instance_of(TornadoOctopus)

    def test_config_parser(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        parser_mock = Mock()

        worker.config_parser(parser_mock)

        parser_mock.add_argument.assert_called_once_with(
            '--concurrency',
            '-t',
            type=int,
            default=10,
            help='Number of threads (or async http requests) to use for Octopus (doing GETs concurrently)'
        )

    def test_proxies_property(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expect(worker.proxies).to_be_like({
            'http': 'http://proxy:8080',
            'https': 'http://proxy:8080'
        })

    def test_async_get(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        otto_mock = Mock()
        worker.otto = otto_mock

        worker.async_get("url", "handler", 'GET', test="test")
        otto_mock.enqueue.assert_called_once_with('url', 'handler', 'GET', test='test', proxies={
            'http': 'http://proxy:8080',
            'https': 'http://proxy:8080'
        })

    def test_tornado_async_get(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        otto_mock = Mock()
        worker.otto = otto_mock

        worker.tornado_async_get("url", "handler", 'GET', test="test")
        otto_mock.enqueue.assert_called_once_with('url', 'handler', 'GET', test='test', proxy_host='http://proxy', proxy_port=8080)

    @patch.object(holmes.worker.requests, 'get')
    def test_get(self, get_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        worker.get('url')

        get_mock.assert_called_once_with('http://localhost:2368/url')

    @patch.object(holmes.worker.requests, 'post')
    def test_post(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        worker.post('url', data={'test': 'test'})

        post_mock.assert_called_once_with(
            'http://localhost:2368/url',
            data={'test': 'test'})

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

        expect(logging_mock.error.call_args_list).to_include(call('Fail to review some-url: '))
        expect(logging_mock.error.call_args_list).to_include(call('Fail to complete worker.'))

    @patch.object(holmes.worker.requests, 'post')
    def test_ping_api(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()

        worker._ping_api()

        post_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/alive' % str(worker.uuid),
            data={}
        )

    @patch.object(holmes.worker.HolmesWorker, 'stop_work')
    @patch.object(holmes.worker.requests, 'post')
    def test_ping_api_when_post_fails(self, post_mock, stop_work_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        post_mock.side_effect = ConnectionError()

        expect(worker._ping_api()).to_be_false()
        stop_work_mock.assert_calls([])

    @patch.object(holmes.worker.HolmesWorker, 'get')
    def test_load_next_job_when_no_job_available(self, get_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        get_mock.return_value = None

        expect(worker._load_next_job()).to_be_null()

    @patch.object(holmes.worker.HolmesWorker, 'get')
    def test_load_next_job_when_job_available_but_no_text(self, get_mock):
        response_mock = Mock(text=None)
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        get_mock.return_value = response_mock

        expect(worker._load_next_job()).to_be_null()

    @patch.object(holmes.worker.HolmesWorker, 'get')
    def test_load_next_job_when_job_available_with_text(self, get_mock):
        response_mock = Mock(text="[0, 1, 2]")
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        get_mock.return_value = response_mock

        expect(worker._load_next_job()).to_be_like([0, 1, 2])

    @patch.object(holmes.worker.HolmesWorker, 'stop_work')
    @patch.object(holmes.worker.HolmesWorker, 'get')
    def test_load_next_job_when_connection_error(self, get_mock, stop_work_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        get_mock.side_effect = ConnectionError()

        expect(worker._load_next_job()).to_be_null()
        stop_work_mock.assert_calls([])

    def test_start_job_when_url_is_none(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()

        expect(worker._start_job(None)).to_be_false()

    @patch.object(holmes.worker.HolmesWorker, 'post')
    def test_start_job_when_url_available(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        post_mock.return_value = Mock(text='OK')

        expect(worker._start_job('http://www.globo.com')).to_be_true()

        post_mock.assert_called_once_with('/worker/%s/start' % str(worker.uuid), data='http://www.globo.com')

    @patch.object(holmes.worker.HolmesWorker, 'post')
    def test_start_job_when_response_is_not_ok(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        post_mock.return_value = Mock(text='NOT_OK')

        expect(worker._start_job('http://www.globo.com')).to_be_false()

        post_mock.assert_called_once_with('/worker/%s/start' % str(worker.uuid), data='http://www.globo.com')

    @patch.object(holmes.worker.HolmesWorker, 'post')
    def test_start_next_job_when_connection_error(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()
        post_mock.side_effect = ConnectionError()

        expect(worker._start_job('http://www.globo.com')).to_be_false()

    @patch.object(holmes.worker.HolmesWorker, 'post')
    def test_complete_job(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()

        post_mock.return_value = Mock(test='OK')

        expect(worker._complete_job("test")).to_be_false()

        post_mock.assert_called_once_with(
            '/worker/%s/complete' % str(worker.uuid),
            data='{"error":"test"}'
        )

    @patch.object(holmes.worker.HolmesWorker, 'post')
    def test_complete_job_when_connection_error(self, post_mock):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])
        worker.uuid = uuid4()

        post_mock.side_effect = ConnectionError()

        expect(worker._complete_job("test")).to_be_false()

        post_mock.assert_called_once_with(
            '/worker/%s/complete' % str(worker.uuid),
            data='{"error":"test"}'
        )
