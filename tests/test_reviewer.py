#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from mock import Mock
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
        expect(reviewer.html).not_to_be_null()

    @gen_test
    def test_review_finish_review(self):
        domain = yield DomainFactory.create(url="http://www.globo.com")
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

        reviewer = Reviewer(page=page)
        review = reviewer.review()

        yield reviewer.conclude(review)

        expect(review.is_complete).to_be_true()
        expect(review.created_date).to_be_like(datetime.now())
        expect(page.last_review).to_equal(review)

        loaded_review = yield Review.objects.get(review._id)
        expect(loaded_review).not_to_be_null()

        yield loaded_review.load_references()

    @gen_test
    def test_validator_runs_validators(self):
        mock_validator = Mock()
        domain = yield DomainFactory.create(url="http://www.globo.com")
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

        reviewer = Reviewer(page=page, validators=[mock_validator])
        reviewer.review()

        expect(mock_validator.called).to_equal(True)
