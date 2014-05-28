#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml
from mock import Mock, call
from tests.unit.base import ApiTestCase
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.link_with_redirect import (
    LinkWithRedirectValidator
)
from tests.fixtures import PageFactory


class TestLinkWithRedirectValidator(ApiTestCase):

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

        url1 = 'http://globo.com/b.html'
        url2 = 'http://globo.com/a.html'

        content = '<html><a href="%s">Test</a><a href="%s">Test</a></html>' % (
            url1, url2)

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRedirectValidator(reviewer)

        validator.add_violation = Mock()

        status_307 = Mock(status_code=307, text='Temporary Redirect')
        status_302 = Mock(status_code=302, text='Found')

        validator.review.data = {
            'page.links': [
                (url1, status_307),
                (url2, status_302)
            ]
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='link.redirect.307',
                value=307,
                points=10
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='link.redirect.302',
                value=302,
                points=10
            ))

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkWithRedirectValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(2)
        expect('link.redirect.302' in definitions).to_be_true()
        expect('link.redirect.307' in definitions).to_be_true()
