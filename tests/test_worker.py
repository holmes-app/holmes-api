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
