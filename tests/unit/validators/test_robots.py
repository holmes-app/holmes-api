#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
from tornado.testing import gen_test

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.robots import RobotsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestRobotsValidator(ValidatorTestCase):

    @gen_test
    def test_get_robots_from_domain(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain, url="http://www.globo.com/index.html")
        review = yield ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )
        validator = RobotsValidator(reviewer)
        validator.get_response = Mock()

        validator.get_robots_from_domain()

        validator.get_response.assert_called_once_with('http://www.globo.com/robots.txt')

    @gen_test
    def test_add_violation_when_404(self):
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

        result = {
            'url': 'http://www.globo.com/robots.txt',
            'status': 404,
            'content': None,
            'html': None
        }
        validator = RobotsValidator(reviewer)

        validator.get_response = Mock(return_value=result)
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='robots.not_found',
            title='Robots not found',
            description='',
            points=100)

    @gen_test
    def test_add_violation_when_empty(self):
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

        result = {
            'url': 'http://www.globo.com/robots.txt',
            'status': 200,
            'content': None,
            'html': None
        }
        validator = RobotsValidator(reviewer)

        validator.get_response = Mock(return_value=result)
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='robots.empty',
            title='Empty robots file',
            description='',
            points=100)

    @gen_test
    def test_add_fact_when_agent_found(self):
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

        result = {
            'url': 'http://www.globo.com/robots.txt',
            'status': 200,
            'content': 'User-agent: *',
            'html': None
        }
        validator = RobotsValidator(reviewer)

        validator.get_response = Mock(return_value=result)
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()
