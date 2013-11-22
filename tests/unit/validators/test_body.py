#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

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
            title='Page body not found.',
            description='Body was not found on %s' % page.url,
            points=50
        )
