#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from holmes.models import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


# class TestMostCommonViolationsHandler(ApiTestCase):

#     @gen_test
#     def test_can_get_most_common_violations(self):
#         review = ReviewFactory.create()
#         self.db.flush()

#         url = self.get_url(
#             '/page/%s/review/%s/violation' % (
#                 review.page.uuid,
#                 review.uuid
#             )
#         )

#         response = yield self.http_client.fetch(
#             url,
#             method='POST',
#             body='key=test.violation&title=title&description=description&points=20'
#         )

#         expect(response.code).to_equal(200)
#         expect(response.body).to_equal('OK')

#         review = Review.by_uuid(review.uuid, self.db)

#         expect(review).not_to_be_null()
#         expect(review.violations).to_length(1)

          ## TODO: most common violations need to be tested without make a post to violation

#         response = yield self.http_client.fetch(
#             self.get_url('/most-common-violations')
#         )
#         expect(response.code).to_equal(200)

#         returned_json = loads(response.body)
#         expect(returned_json).to_length(len(review.violations))
#         expect(returned_json[0]['name']).to_equal('title')
#         expect(returned_json[0]['count']).to_equal(1)
