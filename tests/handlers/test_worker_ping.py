#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Worker
from tests.base import ApiTestCase
from tests.fixtures import WorkerFactory


class TestWorkerHandler(ApiTestCase):
    
    @gen_test
    def test_worker_ping_can_ping_new_worker(self):
        worker_uuid = uuid4()

        response = yield self.http_client.fetch(
            self.get_url('/worker/ping'),
            method='POST',
            body='worker_uuid=%s' % str(worker_uuid)
        )

        workers = yield Worker.objects.filter(uuid=worker_uuid).find_all()

        expect(workers).to_length(1)

        worker = workers[0]
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))

    @gen_test
    def test_worker_ping_can_ping_existing_worker(self):
        date = datetime(2013, 9, 26, 17, 45, 0)

        worker = yield WorkerFactory.create(last_ping=date)

        response = yield self.http_client.fetch(
            self.get_url('/worker/ping'),
            method='POST',
            body='worker_uuid=%s' % str(worker.uuid)
        )

        workers = yield Worker.objects.filter(uuid=worker.uuid).find_all()
        
        expect(workers).to_length(1)

        worker = workers[0]
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))
        expect(worker.last_ping).to_be_greater_than(date)


