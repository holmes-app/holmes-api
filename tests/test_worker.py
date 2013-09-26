#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from mock import patch
from os.path import abspath, dirname, join
from requests.exceptions import ConnectionError

import holmes.worker
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class WorkerTestCase(ApiTestCase):
    root_path = abspath(join(dirname(__file__), ".."))

    @patch('holmes.worker.HolmesWorker')
    def test_worker_main_function(self, worker_mock):
        holmes.worker.main()
        expect(worker_mock().run.called).to_be_true()

    @patch('holmes.worker.time.sleep')
    def test_worker_sleep_time(self, worker_sleep):
        worker = holmes.worker.HolmesWorker()
        worker.run()
        expect(worker_sleep.called).to_be_true()

    def test_worker_working_flag(self):
        worker = holmes.worker.HolmesWorker()
        
        expect(worker.working).to_be_true()
        worker.stop_work()
        expect(worker.working).to_be_false()

    @patch.object(holmes.worker.HolmesWorker, '_do_work')
    def test_worker_run_keyboard_interrupt(self, do_work_mock):
        do_work_mock.side_effect = KeyboardInterrupt()

        worker = holmes.worker.HolmesWorker()
        worker.run()
        expect(worker.working).to_be_false()

    def test_worker_can_create_an_instance(self):
        worker = holmes.worker.HolmesWorker()
        expect(worker.working).to_be_true()
        expect(worker.config.VALIDATORS).to_equal(set())

    def test_worker_can_parse_opt(self):
        worker = holmes.worker.HolmesWorker()
        expect(worker.options.conf).not_to_equal("test.conf")
        expect(worker.options.verbose).to_equal(0)

        worker._parse_opt(arguments=["-c", "test.conf", "-vv"])
        expect(worker.options.conf).to_equal("test.conf")
        expect(worker.options.verbose).to_equal(2)

    def test_worker_can_create_an_instance_with_config_file(self):
        worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/config/test_one_validator.conf')])
        expect(worker.config.VALIDATORS).to_length(1)

    @patch('holmes.worker.verify_config')
    def test_worker_validating_config_load(self, verify_config_mock):
        worker = holmes.worker.HolmesWorker()
        worker._load_config(verify=True)
        expect(verify_config_mock.called).to_be_true()
        
    def test_worker_logging_config_from_arguments(self):
        worker = holmes.worker.HolmesWorker(["", "-v"])
        log_level = worker._config_logging()
        expect(log_level).to_equal("WARNING")

    def test_worker_logging_config_from_file(self):
        worker = holmes.worker.HolmesWorker(['-c', join(self.root_path, './tests/config/test_one_validator.conf')])
        log_level = worker._config_logging()
        expect(log_level).to_equal("INFO")

    @patch('holmes.reviewer.Reviewer')
    def test_worker_do_work(self, reviewer_mock):
        worker = holmes.worker.HolmesWorker()
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        worker._do_work(page)
        expect(reviewer_mock().called).to_be_true()

    @patch.object(holmes.worker.HolmesWorker, '_ping_api')
    def test_worker_do_work_calling_ping_api(self, ping_api_mock):
        worker = holmes.worker.HolmesWorker()
        worker._do_work()
        expect(ping_api_mock.called).to_be_true()

    @patch('holmes.worker.requests.post')
    def test_worker_ping_api(self, requests_mock):
        worker = holmes.worker.HolmesWorker()
        worker._ping_api()
        expect(requests_mock.called).to_be_true()

    @patch('holmes.worker.requests.post')
    def test_worker_ping_api_connection_error(self, ping_api_mock):
        ping_api_mock.side_effect = ConnectionError()

        worker = holmes.worker.HolmesWorker()
        worker._ping_api()
        expect(worker.working).to_be_false()






