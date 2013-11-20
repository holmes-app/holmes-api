#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4

from preggy import expect

from holmes.models import Worker
from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory, ReviewFactory


class TestWorker(ApiTestCase):

    def test_can_create_worker(self):
        worker = WorkerFactory.create()

        expect(worker.id).not_to_be_null()
        expect(worker.uuid).not_to_be_null()

    def test_worker_model_str(self):
        worker = WorkerFactory.create()

        expect(str(worker)).to_equal('Worker %s' % str(worker.uuid))

    def test_worker_current_review_page(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create(current_review=review)

        loaded_worker = self.db.query(Worker).get(worker.id)
        expect(loaded_worker.current_review.id).to_equal(review.id)

    def test_worker_to_dict(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create(current_review=review)

        worker_dict = worker.to_dict()

        expect(worker_dict['uuid']).to_equal(str(worker.uuid))
        expect(worker_dict['last_ping']).to_equal(str(worker.last_ping))
        expect(worker_dict['current_review']).to_equal(str(review.uuid))
        expect(worker_dict['working']).to_be_true()

    def test_worker_is_working(self):
        review = ReviewFactory.create()
        worker = WorkerFactory.create()
        worker2 = WorkerFactory.create(current_review=review)

        expect(worker.working).to_be_false()
        expect(worker2.working).to_be_true()

    def test_can_get_worker_by_uuid(self):
        worker = WorkerFactory.create()
        WorkerFactory.create()

        loaded_worker = Worker.by_uuid(worker.uuid, self.db)
        expect(loaded_worker.id).to_equal(worker.id)

        invalid_worker = Worker.by_uuid(uuid4(), self.db)
        expect(invalid_worker).to_be_null()
