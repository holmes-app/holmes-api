#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.total_requests import TotalRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestTotalRequestsValidator(ValidatorTestCase):

    def test_can_validate_total_requests_on_globo_html(self):
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

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

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
