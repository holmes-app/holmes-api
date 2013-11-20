#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.anchor_without_any_text import (
    AnchorWithoutAnyTextValidator
)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestAnchorWithoutAnyTextValidator(ValidatorTestCase):

    def test_validate_anchor_without_any_text(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

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

        link = Mock(text='')
        link.get.return_value = 'http://globo.com'

        validator = AnchorWithoutAnyTextValidator(reviewer)
        validator.add_fact = Mock()
        validator.add_violation = Mock()
        validator.review.data = {'page.all_links': [link]}
        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='Empty anchor(s) found',
            title='empty.anchors',
            description='Empty anchors are not good for Search Engines. '
                        'Empty anchors were found for links to: '
                        '<a href="http://globo.com" target="_blank">#1</a>.',
            points=20)
