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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'total.size.js': {'default_value': 0.03},
            'total.requests.js': {'default_value': 1},
        }

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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'total.size.js': {'default_value': 0.03},
            'total.requests.js': {'default_value': 1},
        }

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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'total.size.js': {'default_value': 0.03},
            'total.requests.js': {'default_value': 1},
        }

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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        reviewer.violation_definitions = {
            'total.size.js': {'default_value': 0.03},
            'total.requests.js': {'default_value': 1},
        }

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

        expect(definitions).to_length(2)
        expect('total.size.js' in definitions).to_be_true()
        expect('total.requests.js' in definitions).to_be_true()

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

    def test_can_get_default_violations_values(self):
        config = Config()
        config.MAX_JS_KB_PER_PAGE_AFTER_GZIP = 70
        config.MAX_JS_REQUESTS_PER_PAGE = 5

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = JSRequestsValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('total.size.js')
        expect(violations_values).to_include('total.requests.js')

        expect(violations_values['total.size.js']).to_length(2)
        expect(violations_values['total.requests.js']).to_length(2)

        expect(violations_values['total.size.js']).to_be_like({
            'value': config.MAX_JS_KB_PER_PAGE_AFTER_GZIP,
            'description': config.get_description('MAX_JS_KB_PER_PAGE_AFTER_GZIP')
        })

        expect(violations_values['total.requests.js']).to_be_like({
            'value': config.MAX_JS_REQUESTS_PER_PAGE,
            'description': config.get_description('MAX_JS_REQUESTS_PER_PAGE')
        })
