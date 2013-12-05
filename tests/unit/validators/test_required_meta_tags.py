#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.required_meta_tags import RequiredMetaTagsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestRequiredMetaTagsValidator(ValidatorTestCase):

    def test_can_validate_page_without_required_meta_tag(self):
        config = Config()
        config.REQUIRED_META_TAGS = ['description']

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

        validator = RequiredMetaTagsValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [{'key': None}]
        }

        validator.validate()

        for tag in reviewer.config.REQUIRED_META_TAGS:
            validator.add_violation.assert_called_with(
                key='absent.meta.tags',
                value=[tag],
                points=20
            )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = RequiredMetaTagsValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect('absent.meta.tags' in definitions).to_be_true()
