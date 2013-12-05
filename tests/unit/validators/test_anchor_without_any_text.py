#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.anchor_without_any_text import (
    AnchorWithoutAnyTextValidator
)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestAnchorWithoutAnyTextValidator(ValidatorTestCase):

    def test_validate_anchor_without_any_text(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><a href="http://globo.com"></a><a href="http://globo.com/index.html">teste</a></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        link = Mock()
        link.text_content = Mock(return_value='')
        link.findall = Mock(return_value='')
        link.get.return_value = 'http://globo.com'

        validator = AnchorWithoutAnyTextValidator(reviewer)
        validator.add_fact = Mock()
        validator.add_violation = Mock()
        validator.review.data = {'page.all_links': [link]}
        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='empty.anchors',
            value=['http://globo.com'],
            points=20)

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = AnchorWithoutAnyTextValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect('empty.anchors' in definitions).to_be_true()

        links = ['http://globo.com']
        empy_anchors_message = validator.get_empy_anchors_message(links)

        expect(empy_anchors_message).to_equal(
            'Empty anchors are not good for Search Engines. '
            'Empty anchors were found for links to: '
            '<a href="http://globo.com" target="_blank">#0</a>.'
        )
