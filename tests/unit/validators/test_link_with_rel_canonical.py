#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.link_with_rel_canonical import (
    LinkWithRelCanonicalValidator
)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestLinkWithRelCanonicalValidator(ValidatorTestCase):

    def test_validate(self):
        config = Config()

        page = PageFactory.create(url='http://globo.com/1?item=test')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.meta.canonical',
                value=None,
                points=30
            ))

    def test_force_canonical(self):
        config = Config()
        config.FORCE_CANONICAL = True

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.meta.canonical',
                value=None,
                points=30
            ))

    def test_query_string_without_params(self):
        config = Config()
        config.FORCE_CANONICAL = False

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkWithRelCanonicalValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect('absent.meta.canonical' in definitions).to_be_true()

        message = validator.get_absent_meta_canonical_message(
            'http://globo.com'
        )

        url = 'https://support.google.com/webmasters/answer/139394?hl=en'
        expect(message).to_equal(
            'As can be seen in this page <a href="%s">About rel="canonical"'
            '</a>, it\'s a good practice to include rel="canonical" urls in '
            'the pages for your website.' % url
        )
