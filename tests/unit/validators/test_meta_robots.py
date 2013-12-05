#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.meta_robots import MetaRobotsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestMetaRobotsValidator(ValidatorTestCase):

    def test_can_validate_meta_robots_noindex(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><meta robots="noindex"></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = MetaRobotsValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [{'key': 'robots', 'content': 'noindex'}]
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='presence.meta.robots.noindex',
            points=80
        )

    def test_can_validate_meta_robots_nofollow(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        content = '<html><meta robots="nofollow"></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = MetaRobotsValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [{'key': 'robots', 'content': 'nofollow'}]
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='presence.meta.robots.nofollow',
            points=50)

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = MetaRobotsValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect('presence.meta.robots.noindex' in definitions).to_be_true()
        expect('presence.meta.robots.nofollow' in definitions).to_be_true()
