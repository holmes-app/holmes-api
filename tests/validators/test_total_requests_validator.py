#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, patch
from preggy import expect
from tornado.testing import gen_test

from holmes.reviewer import Reviewer
from holmes.validators.total_requests import TotalRequestsValidator
from tests.base import ValidatorTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestValidator(ValidatorTestCase):
    @gen_test
    def test_gets_proper_facts(self):
        with patch.object(Reviewer, 'get_response') as get_response_mock:
            get_response_mock.return_value = Mock(status_code=200, text=self.get_page('globo.html'))

            domain = yield DomainFactory.create(url="http://www.globo.com")
            page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

            reviewer = Reviewer(page=page)
            review = reviewer.review()

            validator = TotalRequestsValidator(reviewer, review)

            validator.validate()

            expect(review.facts).to_length(1)
