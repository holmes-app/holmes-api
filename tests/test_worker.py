#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from mock import patch

import holmes.worker
from tests.base import ApiTestCase


class WorkerTestCase(ApiTestCase):

    @patch('holmes.worker.HolmesWorker')
    def test_worker_main_function(self, worker_mock):
        holmes.worker.main()
        expect(worker_mock().run.called).to_be_true()


    def test_worker_working_flag(self):
        worker = holmes.worker.HolmesWorker()
        
        expect(worker.working).to_be_false
        worker.stop_work()
        expect(worker.working).to_be_true


    @patch.object(holmes.worker.HolmesWorker,'do_work')
    def test_worker_run_keyboard_interrupt(self, do_work_mock):
        do_work_mock.side_effect = KeyboardInterrupt()

        worker = holmes.worker.HolmesWorker()
        run_output = worker.run()
        expect(run_output).to_be_true
