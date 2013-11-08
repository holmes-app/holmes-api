#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
from tornado.testing import gen_test
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.title import TitleValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestTitleValidator(ValidatorTestCase):

    @gen_test
    def test_can_validate_title(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        validator.add_fact.assert_called_once_with(
            key='page.title',
            value=u'globo.com - Absolutamente tudo sobre not\xedcias, esportes e entretenimento',
            title='Title')

        expect(validator.add_violation.called).to_be_false()

    @gen_test
    def test_can_validate_title_with_size_violation(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )

        content = '<html><title>%s</title></html>' % (('*' * reviewer.config.MAX_TITLE_SIZE) + '*')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        validator.add_fact.assert_called_once_with(
            key='page.title',
            value='%s' % ('*' * reviewer.config.MAX_TITLE_SIZE) + '*',
            title='Title')

        validator.add_violation.assert_called_once_with(
            key='page.title.exceed',
            title='Page title exceed maximum characters (%s).' % reviewer.config.MAX_TITLE_SIZE,
            description="Title tags to long may be truncated in the results",
            points=50)

    @gen_test
    def test_can_validate_empty_title(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.called).to_be_false()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    @gen_test
    def test_can_validate_no_title_tag(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.called).to_be_false()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    @gen_test
    def test_can_validate_empty_html(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.called).to_be_false()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            title='Page title not found.',
            description="Title was not found on %s" % page.url,
            points=50)

    @gen_test
    def test_can_validate_multiple_title(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.called).to_be_false()

        validator.add_violation.assert_called_once_with(
            key='page.title.multiple',
            title='To many titles.',
            description="Page %s has %d titles" % (page.url, 2),
            points=50)
