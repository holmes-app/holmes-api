#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Review
from holmes.reviewer import Reviewer
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestReview(ApiTestCase):
    @gen_test
    def test_review_returns_review_object(self):
        domain = yield DomainFactory.create(url="http://www.globo.com")
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

        reviewer = Reviewer(page=page)
        expect(reviewer.review()).to_be_instance_of(Review)

    @gen_test
    def test_review_gets_content(self):
        domain = yield DomainFactory.create(url="http://www.globo.com")
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

        reviewer = Reviewer(page=page)
        reviewer.review()

        expect(reviewer.status_code).to_equal(200)
        expect(reviewer.content).not_to_be_null()
