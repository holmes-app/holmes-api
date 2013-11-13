#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.required_meta_tags import RequiredMetaTagsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestRequiredMetaTagsValidator(ValidatorTestCase):

    def test_can_validate_page_without_required_meta_tag(self):
        config = Config()
        config.REQUIRED_META_TAGS = ['description']

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
        validator.add_fact = Mock()
        validator.add_violation = Mock()
        validator.validate()

        for tag in reviewer.config.REQUIRED_META_TAGS:
            validator.add_violation.assert_called_with(
                key='absent.meta.%s' % tag,
                title='Meta not present',
                description='Not having meta tag for "%s" is '
                            'damaging for Search Engines.' % tag,
                points=20)
