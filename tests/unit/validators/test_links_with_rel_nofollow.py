#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml
from mock import Mock
from tests.unit.base import ApiTestCase
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.links_with_rel_nofollow import (
    LinkWithRelNofollowValidator
)
from tests.fixtures import PageFactory


class TestLinkWithRelNofollowValidator(ApiTestCase):

    def test_validator(self):

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

        url = 'http://my-site.com/test.html'

        content = '<html><a href="%s" rel="nofollow">Test</a></html>' % url

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelNofollowValidator(reviewer)
        validator.add_violation = Mock()

        validator.review.data = {
            'page.all_links': [{'href': url, 'rel': 'nofollow'}]
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='invalid.links.nofollow',
            value=['http://my-site.com/test.html'],
            points=10
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkWithRelNofollowValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('invalid.links.nofollow' in definitions).to_be_true()

        links_nofollow = validator.get_links_nofollow_parsed_value(
            ['http://my-site.com/test.html']
        )
        expect(links_nofollow).to_equal({
            'links': '<a href="http://my-site.com/test.html" target="_blank">#0</a>'
        })
