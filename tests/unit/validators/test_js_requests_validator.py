#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.js_requests import JSRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestTotalRequestsValidator(ValidatorTestCase):

    def test_can_validate_js_requests_on_globo_html(self):
        config = Config()
        config.MAX_JS_REQUESTS_PER_PAGE = 1
        config.MAX_JS_KB_PER_PAGE_AFTER_GZIP = 0.03

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = JSRequestsValidator(reviewer)
        script = {
            'url': 'some_script.js',
            'status': 200,
            'content': 'var test=1;',
            'html': None
        }
        validator.get_response = Mock(return_value=script)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(3)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=2,
                title='Total JS requests'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0.021484375,
                unit='kb',
                title='Total JS size'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0.037109375,
                unit='kb',
                title='Total JS size gzipped'
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.requests.js',
                title='Too many javascript requests.',
                description='This page has 2 javascript request (1 over limit). '
                            'Having too many requests impose a tax in the browser due to handshakes.',
                points=5
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.size.js',
                title='Javascript size in kb is too big.',
                description="There's 0.04kb of Javascript in this page and that adds up to more download "
                            "time slowing down the page rendering to the user.",
                points=0
            ))

    def test_can_validate_js_requests_zero_requests(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = "<html></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = JSRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(3)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=0,
                title='Total JS requests'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0,
                unit='kb',
                title='Total JS size'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0,
                unit='kb',
                title='Total JS size gzipped'
            ))

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_js_requests_empty_html(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        result = {
            'url': page.url,
            'status': 200,
            'content': None,
            'html': None
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = JSRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(3)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=0,
                title='Total JS requests'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0,
                unit='kb',
                title='Total JS size'
            ))

        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0,
                unit='kb',
                title='Total JS size gzipped'
            ))

        expect(validator.add_violation.called).to_be_false()
