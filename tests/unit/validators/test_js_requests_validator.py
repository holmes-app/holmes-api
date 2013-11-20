#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call, patch
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
                title='Too many javascript requests.',
                description='This page has 2 JavaScript request '
                            '(1 over limit). Having too many requests impose '
                            'a tax in the browser due to handshakes.',
                points=5
            )
        )

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.size.js',
                title='Javascript size in kb is too big.',
                description='There\'s 0.04kb of JavaScript in this page and '
                            'that adds up to more download time slowing down '
                            'the page rendering to the user.',
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
