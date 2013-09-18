#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Review
from holmes.reviewer import Reviewer
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestReview(ApiTestCase):
    def test_review_returns_review_object(self):
        domain = yield DomainFactory.create("http://www.globo.com")
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

        reviewer = Reviewer(page=page)
        expect(reviewer.review()).to_be_instance_of(Review)
