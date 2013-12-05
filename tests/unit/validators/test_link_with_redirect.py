#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml
from mock import Mock
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

        validator.add_violation.assert_calls([
            {'key': 'link.redirect.307',
             'title': 'Link with 307 redirect',
             'description': 'Link with redirect, in most cases, should '
                            'not be used. Redirects were found for '
                            'link: %s.' % url1,
             'points': 10},
            {'key': 'link.redirect.302',
             'title': 'Link with 302 redirect',
             'description': 'Link with redirect, in most cases, should '
                            'not be used. Redirects were found for '
                            'link: %s.' % url2,
             'points': 10}
        ])

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkWithRedirectValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect('link.redirect.302' in definitions).to_be_true()
        expect('link.redirect.307' in definitions).to_be_true()

        link_with_redirect_message = validator.get_link_with_redirect_message(
            302
        )

        expect(link_with_redirect_message).to_equal(
            'Link with redirect, in most cases, should not be used. '
            'Redirects were found for link: 302.'
        )
