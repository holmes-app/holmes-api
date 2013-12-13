#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.body import BodyValidator
from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase


class TestBodyValidator(ValidatorTestCase):

    def test_validate(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = BodyValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.body': []
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.body.not_found',
            value=page.url,
            points=50
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = BodyValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('page.body.not_found' in definitions).to_be_true()
