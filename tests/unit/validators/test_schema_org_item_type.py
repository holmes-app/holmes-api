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
            page_score=0.0,
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
                value=None,
                points=10
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.schema.itemtype',
                value=None,
                points=10
            ))

    def test_has_invalid_itemtype(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'invalid.schema.itemtype': {
                'default_value': ['http://schema.org/AboutPage']
            }
        }

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
                value=None,
                points=10
            ))

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = SchemaOrgItemTypeValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(3)
        expect('absent.schema.itemscope' in definitions).to_be_true()
        expect('absent.schema.itemtype' in definitions).to_be_true()
        expect('absent.schema.itemtype' in definitions).to_be_true()

    def test_no_body_tag(self):
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

        content = '<html></html>'

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

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_default_violations_values(self):
        config = Config()
        config.SCHEMA_ORG_ITEMTYPE = [
            'http://schema.org/WebPage',
            'http://schema.org/AboutPage',
        ]

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = SchemaOrgItemTypeValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('invalid.schema.itemtype')

        expect(violations_values['invalid.schema.itemtype']).to_length(2)

        expect(violations_values['invalid.schema.itemtype']).to_equal({
            'value': config.SCHEMA_ORG_ITEMTYPE,
            'description': config.get_description('SCHEMA_ORG_ITEMTYPE')
        })
