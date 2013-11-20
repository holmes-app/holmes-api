#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.meta_tags import MetaTagsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestMetaTagsValidator(ValidatorTestCase):

    def test_get_meta_tags(self):
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

        validator = MetaTagsValidator(reviewer)
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='absent.metatags',
            title='Meta tags not present',
            description='Not having meta tags is damaging for '
                        'Search Engines.',
            points=100
        )

    def test_can_validate_page_without_meta_tags(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
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

        validator = MetaTagsValidator(reviewer)
        validator.add_fact = Mock()
        validator.add_violation = Mock()
        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='absent.metatags',
            title='Meta tags not present',
            description='Not having meta tags is damaging for Search Engines.',
            points=100)
