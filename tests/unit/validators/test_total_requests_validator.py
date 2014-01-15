#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.total_requests import TotalRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestTotalRequestsValidator(ValidatorTestCase):

    def test_can_validate_total_requests_on_globo_html(self):
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

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        reviewer.content_loaded(page.url, Mock(status_code=200, text=content, headers={}))

        validator = TotalRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(1)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests',
                value=69,
                title='Total requests'
            ))

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_total_requests_zero_requests(self):
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
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        reviewer.content_loaded(page.url, Mock(status_code=200, text=content, headers={}))

        validator = TotalRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(1)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests',
                value=0,
                title='Total requests'
            ))

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_total_requests_empty_html(self):
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
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        reviewer.content_loaded(page.url, Mock(status_code=200, text='', headers={}))

        validator = TotalRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(1)
        expect(validator.add_fact.call_args_list).to_include(
            call(
                key='total.requests',
                value=0,
                title='Total requests'
            ))

        expect(validator.add_violation.called).to_be_false()
