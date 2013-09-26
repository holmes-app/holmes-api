#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from tornado.testing import gen_test

from tests.base import ApiTestCase
from tests.fixtures import WorkerFactory


class TestWorker(ApiTestCase):

    @gen_test
    def test_can_create_worker(self):
        worker = yield WorkerFactory.create()

        expect(worker._id).not_to_be_null()
        expect(worker.uuid).not_to_be_null()
