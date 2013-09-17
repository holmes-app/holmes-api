#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ProcessingFactory


class TestProcessing(ApiTestCase):
    @gen_test
    def test_can_create_processing(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        processing = yield ProcessingFactory.create(page=page)

        expect(processing._id).not_to_be_null()
        expect(processing.created_date).to_be_like(datetime.now())

        expect(processing.page._id).to_equal(page._id)
