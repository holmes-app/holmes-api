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

        content = '<html><body></body></html>'

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
                points=10
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.schema.itemtype',
                points=10
            ))

    def test_has_invalid_itemtype(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><body itemtype="http://schema.org/a"></body></html>'

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
            'page.body': [{'itemtype': 'a'}]
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='invalid.schema.itemtype',
                points=10
            ))

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = SchemaOrgItemTypeValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect('absent.schema.itemscope' in definitions).to_be_true()
        expect('absent.schema.itemtype' in definitions).to_be_true()
        expect('absent.schema.itemtype' in definitions).to_be_true()

        itemscope_message = validator.get_itemscope_message()
        itemtype_message = validator.get_itemtype_message()
        invalid_itemtype_message = validator.get_invalid_itemtype_message()

        expect(itemscope_message).to_equal(
            'In order to conform to schema.org definition of a webpage, the '
            'body tag must feature an itemscope attribute.'
        )

        expect(itemtype_message).to_equal(
            'In order to conform to schema.org definition of a webpage, '
            'the body tag must feature an itemtype attribute.'
        )

        expect(invalid_itemtype_message).to_equal(
            'In order to conform to schema.org definition of a webpage, '
            'the body tag must feature an itemtype attribute with a value '
            'of "http://schema.org/WebPage" or one of its more specific types.'
        )
