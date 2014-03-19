#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Worker
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory


class TestWorkerHandler(ApiTestCase):

    @gen_test
    def test_workers_list(self):
        worker = WorkerFactory.create(current_url='http://www.globo.com/')
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/workers/'),
        )

        expect(response.code).to_equal(200)

        workers = self.db.query(Worker).all()

        returned_json = loads(response.body)
        expect(returned_json).to_length(len(workers))

        expect(returned_json[0]['uuid']).to_equal(str(worker.uuid))
        expect(returned_json[0]['current_url']).to_equal('http://www.globo.com/')
        expect(returned_json[0]['working']).to_be_true()

    @gen_test
    def test_workers_info(self):
        WorkerFactory.create(current_url='http://www.globo.com/')
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/workers/info/'),
        )

        expect(response.code).to_equal(200)

        total_workers = self.db.query(Worker).count()
        inactive_workers = self.db.query(Worker).filter(Worker.current_url == None).count()

        returned_json = loads(response.body)
        expect(returned_json).to_length(3)
        expect(returned_json['total']).not_to_be_null()
        expect(returned_json['active']).not_to_be_null
        expect(returned_json['inactive']).not_to_be_null()

        expect(returned_json['total']).to_equal(total_workers)
        expect(returned_json['active']).to_equal(total_workers - inactive_workers)
        expect(returned_json['inactive']).to_equal(inactive_workers)
