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
                title='Too many CSS requests.',
                description='This page has 7 CSS request (6 over limit). '
                            'Having too many requests impose a tax in the browser due to handshakes.',
                points=30
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.size.css',
                title='CSS size in kb is too big.',
                description="There's 0.05kb of CSS in this page and that adds up to more download time "
                            "slowing down the page rendering to the user.",
                points=0
            ))

    def test_can_validate_css_requests_zero_requests(self):
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
