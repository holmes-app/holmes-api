#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.js_requests import JSRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestTotalRequestsValidator(ValidatorTestCase):

    def test_can_validate_js_requests_on_globo_html(self):
        config = Config()
        config.MAX_JS_REQUESTS_PER_PAGE = 1
        config.MAX_JS_KB_PER_PAGE_AFTER_GZIP = 0.03

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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
        validator.add_violation = Mock()
        validator.review.data = {
            'total.requests.js': 2,
            'total.size.js.gzipped': 0.04,
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.requests.js',
                value={'total_js_files': 2, 'over_limit': 1},
                points=5
            )
        )

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0.04,
                points=0
            ))

    def test_can_validate_js_requests_zero_requests(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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

        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_js_requests_empty_html(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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

        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        config = Config()
        config.MAX_JS_REQUESTS_PER_PAGE = 1
        config.MAX_JS_KB_PER_PAGE_AFTER_GZIP = 0.03

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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

        definitions = validator.get_violation_definitions()

        expect('total.size.js' in definitions).to_be_true()
        expect('total.requests.js' in definitions).to_be_true()

        total_size_message = validator.get_total_size_message(0.03)
        requests_js_message = validator.get_requests_js_message({
            'total_js_files': 7,
            'over_limit': 6
        })

        expect(total_size_message).to_equal(
            'There\'s 0.03kb of JavaScript in this page and that adds '
            'up to more download time slowing down the page rendering '
            'to the user.'
        )

        expect(requests_js_message).to_equal(
            'This page has 7 JavaScript request (6 over limit). Having too '
            'many requests impose a tax in the browser due to handshakes.'
        )

    def test_get_js_requests(self):
        reviewer = Mock()
        validator = JSRequestsValidator(reviewer)
        validator.review.data = {
            'page.js': []
        }

        js_requests = validator.get_js_requests()

        expect(js_requests).to_equal([])

    def test_get_total_size_js(self):
        reviewer = Mock()
        validator = JSRequestsValidator(reviewer)
        validator.review.data = {
            'total.size.js': 100
        }

        total_size = validator.get_total_size_js()

        expect(total_size).to_equal(100)
