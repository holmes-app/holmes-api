#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.title import TitleValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestTitleValidator(ValidatorTestCase):

    def test_can_validate_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.title.count': 1
        }

        validator.review.facts = {
            'page.title': ['the title']
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_empty_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        content = '<html><title></title></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    def test_can_validate_no_title_tag(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
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

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    def test_can_validate_empty_html(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        content = ''

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': None
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    def test_can_validate_multiple_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        content = '<html><title>Ping</title><title>Pong</title></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()
        validator.review.data = {
            'page.title.count': 2
        }

        validator.review.facts = {
            'page.title': ['first', 'second']
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.multiple',
            title='To many titles.',
            description="Page %s has %d titles" % (page.url, 2),
            points=50)
