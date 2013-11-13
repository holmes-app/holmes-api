#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from ujson import loads
from datetime import datetime, timedelta

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Worker
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory, PageFactory, ReviewFactory


class TestWorkerHandler(ApiTestCase):

    @gen_test
    def test_worker_alive_can_add_new_worker(self):
        worker_uuid = uuid4()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/alive' % str(worker_uuid)),
            method='POST',
            body=''
        )

        worker = Worker.by_uuid(worker_uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))

    @gen_test
    def test_worker_alive_can_ping_existing_worker(self):
        date = datetime.now()

        worker = WorkerFactory.create(last_ping=date)
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/worker/%s/alive' % str(worker.uuid)),
            method='POST',
            body='current_review=%s' % str(worker.current_review)
        )

        worker = Worker.by_uuid(worker.uuid, self.db)

        expect(worker).not_to_be_null()
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(str(worker.uuid))
        expect(worker.last_ping).to_be_greater_than(date)

    @gen_test
    def test_worker_removal_after_long_time_without_ping_alive(self):
        date = datetime.now()-timedelta(seconds=300)
        worker_old = WorkerFactory.create(last_ping=date)
        worker_new = WorkerFactory.create()
        self.db.flush()

        yield self.http_client.fetch(
            self.get_url('/worker/%s/alive' % str(worker_new.uuid)),
            method='POST',
            body=''
        )

        response = yield self.http_client.fetch(
            self.get_url('/workers/'),
        )

        returned_json = loads(response.body)
        expect(returned_json).not_to_be_null()
        expect(returned_json).to_length(1)
        expect(returned_json[0]['uuid']).not_to_equal(str(worker_old.uuid))

    @gen_test
    def test_worker_removal_when_ping_will_die(self):
        worker_old = WorkerFactory.create()
        worker_dead = WorkerFactory.create()
        self.db.flush()

        yield self.http_client.fetch(
            self.get_url('/worker/%s/dead' % str(worker_dead.uuid)),
            method='POST',
            body=''
        )

        response = yield self.http_client.fetch(
            self.get_url('/workers/'),
        )

        returned_json = loads(response.body)
        expect(returned_json).not_to_be_null()
        expect(returned_json).to_length(1)
        expect(returned_json[0]['uuid']).not_to_equal(str(worker_dead.uuid))
        expect(returned_json[0]['uuid']).to_equal(str(worker_old.uuid))

    @gen_test
    def test_workers_list(self):
        page = PageFactory.create()

        review = ReviewFactory.create(page=page)
        worker = WorkerFactory.create(current_review=review)
        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/workers/'),
        )

        expect(response.code).to_equal(200)

        workers = self.db.query(Worker).all()

        returned_json = loads(response.body)
        expect(returned_json).to_length(len(workers))

        expect(returned_json[0]['uuid']).to_equal(str(worker.uuid))
        expect(returned_json[0]['current_review']).to_equal(str(review.uuid))
        expect(returned_json[0]['working']).to_be_true()
        expect(returned_json[0]['page_url']).to_equal(page.url)
        expect(returned_json[0]['page_uuid']).to_equal(str(page.uuid))
