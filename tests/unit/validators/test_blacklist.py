#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml
from mock import Mock
from preggy import expect

from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase
from holmes.reviewer import Reviewer
from holmes.config import Config
from holmes.validators.blacklist import BlackListValidator


class TestBlackListValidator(ValidatorTestCase):

    def test_can_validate(self):
        config = Config()
        config.BLACKLIST_DOMAIN = ['a.com']

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        content = '<a href="http://a.com/test1">A</a>' \
                  '<a href="http://b.com/test2">B</a>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = BlackListValidator(reviewer)
        validator.review.data = {
            'page.all_links': [
                {'href': 'http://a.com/test1'}, {'href': 'http://b.com/test2'}
            ]
        }

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            points=100,
            key='blacklist.domains',
            value=['http://a.com/test1']
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = BlackListValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('blacklist.domains' in definitions).to_be_true()

        expect(validator.get_blacklist_parsed_value(['http://a.com'])).to_equal(
            '<a href="http://a.com" target="_blank">Link #0</a>'
        )
