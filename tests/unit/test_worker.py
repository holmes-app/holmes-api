#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

from preggy import expect
from mock import patch, Mock
from requests.exceptions import ConnectionError
from tornado.testing import gen_test
import requests

import holmes.worker
from holmes.config import Config
from holmes.reviewer import InvalidReviewError
from holmes.validators.base import Validator
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class MockResponse(object):
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text


class WorkerTestCase(ApiTestCase):
    root_path = abspath(join(dirname(__file__), '..', '..'))

    def get_worker(self):
        worker = holmes.worker.HolmesWorker()
        worker.config = Config(**self.get_config())
        return worker

    def get_config(self):
        cfg = super(WorkerTestCase, self).get_config()
        cfg['WORKER_SLEEP_TIME'] = 1
        cfg['HOLMES_API_URL'] = 'http://localhost:2368'
        cfg['VALIDATORS'] = ['holmes.validators.js_requests.JSRequestsValidator',
                             'holmes.validators.total_requests.TotalRequestsValidator',
                             ]
        return cfg

    @patch('holmes.worker.HolmesWorker')
    def test_worker_main_function(self, worker_mock):
        holmes.worker.main()
        expect(worker_mock().run.called).to_be_true()

    @patch('time.sleep')
    def test_worker_sleep_time(self, worker_sleep):
        worker = self.get_worker()
        worker._do_work = Mock()
        worker_sleep.side_effect = lambda *args: worker.stop_work()
        worker.run()
        worker_sleep.assert_called_once_with(1)

    @patch('requests.post')
    def test_worker_working_flag(self, requests_mock):
        worker = self.get_worker()

        expect(worker.working).to_be_true()
        worker.stop_work()
        expect(worker.working).to_be_false()

        expect(requests_mock.called).to_be_true()
        requests_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/dead' % worker.uuid,
            data={'worker_uuid': worker.uuid}
        )

    @patch.object(holmes.worker.HolmesWorker, '_do_work')
    def test_worker_run_keyboard_interrupt(self, do_work_mock):
        do_work_mock.side_effect = KeyboardInterrupt()

        worker = self.get_worker()
        worker.run()
        expect(worker.working).to_be_false()

    def test_worker_can_create_an_instance(self):
        worker = holmes.worker.HolmesWorker()
        expect(worker.working).to_be_true()

    def test_worker_can_parse_opt(self):
        worker = self.get_worker()
        expect(worker.options.conf).not_to_equal('test.conf')
        expect(worker.options.verbose).to_equal(0)

        worker._parse_opt(arguments=['-c', 'test.conf', '-vv'])
        expect(worker.options.conf).to_equal('test.conf')
        expect(worker.options.verbose).to_equal(2)

    def test_worker_can_create_an_instance_with_config_file(self):
        worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/unit/config/test_one_validator.conf')])
        expect(worker.config.VALIDATORS).to_length(1)

    @patch('holmes.worker.verify_config')
    def test_worker_validating_config_load(self, verify_config_mock):
        worker = self.get_worker()
        worker._load_config(verify=True)
        expect(verify_config_mock.called).to_be_true()

    def test_worker_logging_config_from_arguments(self):
        worker = holmes.worker.HolmesWorker(['', '-v'])
        log_level = worker._config_logging()
        expect(log_level).to_equal('WARNING')

    def test_worker_logging_config_from_file(self):
        worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/unit/config/test_one_validator.conf')])
        log_level = worker._config_logging()
        expect(log_level).to_equal('INFO')

    def test_worker_do_work(self):
        worker = self.get_worker()

        worker._ping_api = Mock()
        job = {'page': self.ZERO_UUID, 'review': self.ZERO_UUID, 'url': 'http://globo.com'}
        worker._load_next_job = Mock(return_value=job)
        worker._start_job = Mock()
        worker._start_reviewer = Mock()
        worker._complete_job = Mock()

        worker._do_work()

        expect(worker._ping_api.called).to_be_true()
        expect(worker._load_next_job.called).to_be_true()
        expect(worker._start_job.called).to_be_true()
        worker._start_job.assert_called_once_with(self.ZERO_UUID)
        worker._start_reviewer.assert_called_once_with(job=job)
        worker._complete_job.assert_called_once_with(self.ZERO_UUID, error=None)

    @patch.object(holmes.worker.HolmesWorker, '_ping_api')
    def test_worker_do_work_calling_ping_api(self, ping_api_mock):
        worker = holmes.worker.HolmesWorker()
        worker._load_next_job = Mock(return_value=None)
        worker._do_work()
        expect(ping_api_mock.called).to_be_true()

    @patch('requests.post')
    def test_worker_ping_api(self, requests_mock):
        worker = self.get_worker()
        worker._ping_api()
        expect(requests_mock.called).to_be_true()
        requests_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/alive' % worker.uuid,
            data={'worker_uuid': worker.uuid}
        )

    @patch('requests.post')
    def test_worker_ping_api_connection_error(self, ping_api_mock):
        ping_api_mock.side_effect = ConnectionError()
        worker = self.get_worker()
        worker._do_work()
        expect(worker.working).to_be_false()

    @patch('requests.post')
    def test_worker_load_next_job_error(self, load_next_job_mock):
        load_next_job_mock.side_effect = ConnectionError()
        worker = self.get_worker()
        worker._load_next_job()
        expect(worker.working).to_be_false()

    @patch('requests.post')
    def test_worker_load_next_job_must_call_api(self, load_next_job_mock):
        response = MockResponse(200, '')
        load_next_job_mock.return_value = response
        worker = self.get_worker()
        worker._load_next_job()

        expect(load_next_job_mock.called).to_be_true()
        load_next_job_mock.assert_called_once_with('http://localhost:2368/next', data={})

    @patch('requests.post')
    def test_worker_load_next_job_without_jobs(self, load_next_job_mock):
        response = MockResponse(200, '')
        load_next_job_mock.return_value = response
        worker = self.get_worker()
        next_job = worker._load_next_job()

        expect(next_job).to_be_null()

    @gen_test
    def test_worker_load_next_job(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        expected = '{"page": "%s", "review": "%s", "url": "%s"}' % (
            str(page.uuid),
            str(review.uuid),
            page.url
        )

        response = MockResponse(200, expected)

        requests.post = Mock(return_value=response)

        worker = holmes.worker.HolmesWorker()
        next_job = worker._load_next_job()

        expect(next_job).not_to_be_null()
        expect(next_job['page']).to_equal(str(page.uuid))
        expect(next_job['review']).to_equal(str(review.uuid))
        expect(next_job['url']).to_equal(str(page.url))

    @patch('requests.post')
    def test_worker_start_error(self, load_start_job_mock):
        load_start_job_mock.side_effect = ConnectionError()
        worker = self.get_worker()
        worker._start_job(self.ZERO_UUID)
        expect(worker.working).to_be_true()

    @patch('requests.post')
    def test_worker_start_call_api(self, requests_mock):
        response = MockResponse(200, 'OK')
        requests_mock.return_value = response
        worker = self.get_worker()
        result = worker._start_job(self.ZERO_UUID)
        expect(requests_mock.called).to_be_true()
        requests_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/review/%s/start' % (str(worker.uuid), self.ZERO_UUID)
        )
        expect(result).to_be_true()

    @patch('requests.post')
    def test_worker_start_null_job(self, requests_mock):
        response = MockResponse(200, 'OK')
        requests_mock.return_value = response
        worker = self.get_worker()
        result = worker._start_job(None)
        expect(requests_mock.called).to_be_false()
        expect(result).to_be_false()

    @patch('requests.post')
    def test_worker_complete_error(self, load_start_job_mock):
        load_start_job_mock.side_effect = ConnectionError()
        worker = self.get_worker()
        worker._complete_job(self.ZERO_UUID)
        expect(worker.working).to_be_true()

    @patch('requests.post')
    def test_worker_complete_call_api(self, requests_mock):
        response = MockResponse(200, 'OK')
        requests_mock.return_value = response
        worker = self.get_worker()
        worker._complete_job(self.ZERO_UUID)
        requests_mock.assert_called_once_with(
            'http://localhost:2368/worker/%s/review/%s/complete' % (str(worker.uuid), self.ZERO_UUID),
            data='{"error":null}')

    @patch('requests.post')
    def test_worker_complete_null_job(self, requests_mock):
        response = MockResponse(200, 'OK')
        requests_mock.return_value = response
        worker = self.get_worker()
        result = worker._complete_job(None)
        expect(requests_mock.called).to_be_false()
        expect(result).to_be_false()

    def test_do_work_without_next_job(self):
        worker = self.get_worker()

        job = None
        worker._load_next_job = Mock(return_value=job)
        worker._ping_api = Mock(return_value=True)
        worker._start_job = Mock()
        worker._complete_job = Mock()

        worker._do_work()

        expect(worker._start_job.called).to_be_false()
        expect(worker._complete_job.called).to_be_false()

    @gen_test
    def test_do_work_with_next_job(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        worker = self.get_worker()

        job = {'page': str(page.uuid), 'review': str(review.uuid), 'url': page.url}
        worker._load_next_job = Mock(return_value=job)
        worker._ping_api = Mock(return_value=True)
        worker._start_job = Mock()
        worker._start_reviewer = Mock()
        worker._complete_job = Mock()

        worker._do_work()

        expect(worker._start_job.called).to_be_true()
        expect(worker._complete_job.called).to_be_true()

    @gen_test
    def test_do_work_invalid_review_error(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        worker = self.get_worker()

        job = {'page': str(page.uuid), 'review': str(review.uuid), 'url': page.url}
        worker._load_next_job = Mock(return_value=job)
        worker._ping_api = Mock(return_value=True)
        worker._start_job = Mock()
        worker._start_reviewer = Mock(side_effect=InvalidReviewError)
        worker._complete_job = Mock()

        worker._do_work()

        expect(worker._start_job.called).to_be_true()
        expect(worker._complete_job.called).to_be_true()

    def test_load_validators_none(self):
        worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/unit/config/test_empty_conf.conf')])
        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(0)

    def test_load_validators(self):
        worker = self.get_worker()

        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(2)

        for validator in validators:
            try:
                expect(issubclass(validator, Validator)).to_be_true()
            except TypeError:
                assert False, 'Expect all validators to be subclass of holmes.validators.base.Validator'

    def test_load_validators_can_instantiate_a_validator(self):
        worker = self.get_worker()
        worker.config.VALIDATORS = ['holmes.validators.js_requests.JSRequestsValidator']

        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(1)

        validator_class = validators[0]
        validator = validator_class(None)
        expect(type(validator)).to_equal(holmes.validators.js_requests.JSRequestsValidator)

    def test_load_validators_invalid_validator_full_name(self):
        worker = self.get_worker()
        worker.config.VALIDATORS += ['JSRequestsValidator']

        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(2)

    def test_load_validators_unknown_class(self):
        worker = self.get_worker()
        worker.config.VALIDATORS += ['holmes.validators.js_requests.ValidatorDoesNotExist']

        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(2)

    def test_load_validators_unknown_module(self):
        worker = self.get_worker()
        worker.config.VALIDATORS += ['holmes.validators.unknown_module.ValidatorDoesNotExist']

        validators = worker._load_validators()

        expect(validators).not_to_be_null()
        expect(validators).to_length(2)

    @patch("holmes.reviewer.Reviewer.review")
    def test_start_reviwer_without_job(self, mock_reviewer):
        worker = self.get_worker()
        worker._start_reviewer(None)
        expect(mock_reviewer.called).not_to_be_true()

    @patch("holmes.reviewer.Reviewer.review")
    def test_start_reviwer(self, mock_reviewer):
        worker = self.get_worker()
        worker._load_validators = Mock(return_value=[])
        job = {'page': self.ZERO_UUID, 'review': self.ZERO_UUID, 'url': 'http://globo.com'}
        worker._start_reviewer(job=job)
        expect(mock_reviewer.called).to_be_true()
