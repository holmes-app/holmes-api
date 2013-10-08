#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, patch
from preggy import expect
from tornado.testing import gen_test

from holmes.reviewer import Reviewer
from holmes.validators.js_requests import JSRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import DomainFactory, PageFactory


#class TestValidator(ValidatorTestCase):
    #@gen_test
    #def test_gets_proper_facts(self):
        #config_mock = Mock(
            #MAX_JS_REQUESTS_PER_PAGE=1,
            #MAX_JS_KB_PER_PAGE_AFTER_GZIP=5
        #)

        #with patch.object(Reviewer, 'get_response') as get_response_mock:
            #get_response_mock.return_value = Mock(status_code=200, text=self.get_page('globo.html'))

            #domain = yield DomainFactory.create(url="http://www.globo.com")
            #page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

            #reviewer = Reviewer(page=page, config=config_mock)
            #review = reviewer.review()

        #validator = JSRequestsValidator(reviewer, review)

        #validator.validate()

        #expect(review.facts).to_length(3)

        #expect(review.facts[0].key).to_equal('total.requests.js')
        #expect(review.facts[0].value).to_equal(2)
        #expect(review.facts[0].unit).to_equal('value')

        #expect(review.facts[1].key).to_equal('total.size.js')
        #expect(review.facts[1].value).to_be_like(38.3701171875)
        #expect(review.facts[1].unit).to_equal('kb')

        #expect(review.facts[2].key).to_equal('total.size.js.gzipped')
        #expect(review.facts[2].value).to_be_like(13.3212890625)
        #expect(review.facts[2].unit).to_equal('kb')

        #expect(review.violations).to_length(2)

        #expect(review.violations[0].key).to_equal('total.requests.js')
        #expect(review.violations[0].title).to_equal('Too many javascript requests.')
        #expect(review.violations[0].description).to_equal('This page has 2 javascript request (1 over limit). Having too many requests impose a tax in the browser due to handshakes.')
        #expect(review.violations[0].points).to_equal(5)  # number of js requests over the limit * 5

        #expect(review.violations[1].key).to_equal('total.size.js')
        #expect(review.violations[1].title).to_equal('Javascript size in kb is too big.')
        #expect(review.violations[1].description).to_equal("There's 13.32kb of Javascript in this page and that adds up to more download time slowing down the page rendering to the user.")
        #expect(review.violations[1].points).to_equal(8)  # size over the limit rounded down

    #@gen_test
    #def test_gets_proper_facts_no_violations(self):
        #config_mock = Mock(
            #MAX_JS_REQUESTS_PER_PAGE=2,
            #MAX_JS_KB_PER_PAGE_AFTER_GZIP=15
        #)

        #with patch.object(Reviewer, 'get_response') as get_response_mock:
            #get_response_mock.return_value = Mock(status_code=200, text=self.get_page('globo.html'))

            #domain = yield DomainFactory.create(url="http://www.globo.com")
            #page = yield PageFactory.create(domain=domain, url="http://www.globo.com/")

            #reviewer = Reviewer(page=page, config=config_mock)
            #review = reviewer.review()

        #validator = JSRequestsValidator(reviewer, review)

        #validator.validate()

        #expect(review.facts).to_length(3)

        #expect(review.facts[0].key).to_equal('total.requests.js')
        #expect(review.facts[0].value).to_equal(2)
        #expect(review.facts[0].unit).to_equal('value')

        #expect(review.facts[1].key).to_equal('total.size.js')
        #expect(review.facts[1].value).to_be_like(38.3701171875)
        #expect(review.facts[1].unit).to_equal('kb')

        #expect(review.facts[2].key).to_equal('total.size.js.gzipped')
        #expect(review.facts[2].value).to_be_like(13.3212890625)
        #expect(review.facts[2].unit).to_equal('kb')

        #expect(review.violations).to_length(0)

