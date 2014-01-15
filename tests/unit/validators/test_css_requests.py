#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.css_requests import CSSRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestCSSRequestsValidator(ValidatorTestCase):

    def test_can_validate_css_requests_on_globo_html(self):
        config = Config()
        config.MAX_CSS_REQUESTS_PER_PAGE = 1
        config.MAX_CSS_KB_PER_PAGE_AFTER_GZIP = 0.0

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
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

        validator = CSSRequestsValidator(reviewer)
        css = {
            'url': 'some_style.css',
            'status': 200,
            'content': '#id{display:none}',
            'html': None
        }
        validator.get_response = Mock(return_value=css)

        validator.add_violation = Mock()

        validator.review.data = {
            'total.requests.css': 7,
            'total.size.css.gzipped': 0.05
        }
        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.requests.css',
                value={'over_limit': 6, 'total_css_files': 7},
                points=30
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.size.css',
                value=0.05,
                points=0
            ))

    def test_can_validate_css_requests_zero_requests(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
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

        validator = CSSRequestsValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_css_requests_empty_html(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
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

        validator = CSSRequestsValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = CSSRequestsValidator(reviewer)

        definitions = validator.get_violation_definitions()
        total_size_message = validator.get_total_size_message(0.05)
        requests_css_message = validator.get_requests_css_message({
            'total_css_files': 7,
            'over_limit': 6
        })

        expect(total_size_message).to_equal(
            'There\'s 0.05kb of CSS in this page and that adds up to more '
            'download time slowing down the page rendering to the user.'
        )

        expect(requests_css_message).to_equal(
            'This page has 7 CSS request (6 over limit). Having too many '
            'requests impose a tax in the browser due to handshakes.'
        )

        expect(definitions).to_length(2)
        expect('total.size.css' in definitions).to_be_true()
        expect('total.requests.css' in definitions).to_be_true()

    def test_get_css_requests(self):
        reviewer = Mock()
        validator = CSSRequestsValidator(reviewer)

        css1 = Mock()
        css2 = Mock()
        validator.review.data = {
            'page.css': [css1, css2]
        }

        css_requests = validator.get_css_requests()

        expect(css_requests).to_equal([css1, css2])
