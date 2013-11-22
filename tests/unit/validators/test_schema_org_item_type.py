#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.schema_org_item_type import (
    SchemaOrgItemTypeValidator
)
from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase


class TestSchemaOrgItemTypeValidator(ValidatorTestCase):

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

        content = '<html><body></body</html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = SchemaOrgItemTypeValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.body': [{}]
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.schema.itemscope',
                title='itemscope attribute missing in body',
                description='In order to conform to schema.org definition '
                            'of a webpage, the body tag must feature an '
                            'itemscope attribute.',
                points=10
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.schema.itemtype',
                title='itemtype attribute missing in body',
                description='In order to conform to schema.org definition '
                            'of a webpage, the body tag must feature an '
                            'itemtype attribute.',
                points=10
            ))

        url = 'http://schema.org/WebPage'
        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='invalid.schema.itemtype',
                title='itemtype attribute is invalid',
                description='In order to conform to schema.org definition '
                            'of a webpage, the body tag must feature an '
                            'itemtype attribute with a value of "%s" or '
                            'one of its more specific types.' % (url),
                points=10
            ))
