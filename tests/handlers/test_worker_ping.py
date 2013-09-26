#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tests.base import ApiTestCase
from uuid import uuid1


class TestReview(ApiTestCase):
    def test_worker_ping_can_ping(self):
        worker_uuid = uuid1().hex

        response = self.fetch('/worker/ping',
                              method='POST',
                              body='worker_uuid=%s' % worker_uuid
                              )
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like(worker_uuid)
