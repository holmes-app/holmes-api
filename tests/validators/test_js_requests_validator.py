#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, patch
from preggy import expect
from tornado.testing import gen_test

from holmes.reviewer import Reviewer
from holmes.validators.js_requests import JSRequestsValidator
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

        validator = JSRequestsValidator(reviewer, review)

        validator.validate()

        expect(review.facts).to_length(3)

        expect(review.facts[0].key).to_equal('total.requests.js')
        expect(review.facts[0].value).to_equal(2)
        expect(review.facts[0].unit).to_equal('value')

        expect(review.facts[1].key).to_equal('total.size.js')
        expect(review.facts[1].value).to_be_like(38.3701171875)
        expect(review.facts[1].unit).to_equal('kb')

        expect(review.facts[2].key).to_equal('total.size.js.gzipped')
        expect(review.facts[2].value).to_be_like(13.3212890625)
        expect(review.facts[2].unit).to_equal('kb')
