#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.meta_robots import MetaRobotsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestMetaRobotsValidator(ValidatorTestCase):

    def test_can_validate_meta_robots_noindex(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='presence.meta.robots.noindex',
            title='Meta Robots with value of noindex',
            description='A meta tag with the robots="noindex" '
                        'attribute tells the search engines that '
                        'they should not index this page.',
            points=80)

    def test_can_validate_meta_robots_nofollow(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
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

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='presence.meta.robots.nofollow',
            title='Meta Robots with value of nofollow',
            description='A meta tag with the robots="nofollow" '
                        'attribute tells the search engines that they '
                        'should not follow any links in this page.',
            points=50)
