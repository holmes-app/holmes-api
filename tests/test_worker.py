#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from mock import patch

import holmes.worker
from tests.base import ApiTestCase


class WorkerTestCase(ApiTestCase):

    @patch('holmes.worker.HolmesWorker')
    def test_server_main_function(self, worker_mock):
        holmes.worker.main()
        expect(worker_mock.run.called).to_be_true()
