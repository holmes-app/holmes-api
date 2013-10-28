#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from tornado.testing import gen_test

from tests.unit.base import ApiTestCase
from tests.fixtures import WorkerFactory, PageFactory, DomainFactory, ReviewFactory


class TestWorker(ApiTestCase):

    @gen_test
    def test_can_create_worker(self):
        worker = yield WorkerFactory.create()

        expect(worker._id).not_to_be_null()
        expect(worker.uuid).not_to_be_null()

    @gen_test
    def test_worker_model_str(self):
        worker = yield WorkerFactory.create()

        expect(str(worker)).to_equal('Worker %s' % str(worker.uuid))

    @gen_test
    def test_worker_current_review_page(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)
        worker = yield WorkerFactory.create(current_review=review)

        expect(worker.current_review.page).to_equal(page)

    def test_worker_to_dict(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)
        worker = yield WorkerFactory.create(current_review=review)

        worker_dict = worker.to_dict()

        expect(worker_dict['uuid']).to_equal(str(worker.uuid))
        expect(worker_dict['last_ping']).to_equal(str(self.last_ping))
        expect(worker_dict['current_review']).to_equal(str(review.uuid))
        expect(worker_dict['working']).to_be_true()
