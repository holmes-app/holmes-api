#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.meta_tags import MetaTagsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestMetaTagsValidator(ValidatorTestCase):

    def test_can_validate_pages_with_metatags(self):
        page = PageFactory.create()
        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        validator = MetaTagsValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data['meta.tags'] = [
            {'content': 'utf-8', 'property': None, 'key': 'charset'},
            {'content': 'text/html;charset=UTF-8', 'property': 'http-equiv', 'key': 'Content-Type'},
        ]
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_page_without_meta_tags(self):
        page = PageFactory.create()
        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        validator = MetaTagsValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data['meta.tags'] = []
        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='absent.metatags',
            value='No metatags.',
            points=100
        )

    def test_can_validate_page_with_metatag_description_too_long(self):
        page = PageFactory.create()
        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        validator = MetaTagsValidator(reviewer)

        validator.add_violation = Mock()
        validator.review.data['meta.tags'] = [
            {'content': 'X' * 301, 'property': 'name', 'key': 'description'},
        ]
        validator.validate()
        validator.add_violation.assert_called_once_with(
            key='page.metatags.description_too_big',
            value={'max_size': 300},
            points=20
        )

        validator.add_violation = Mock()
        validator.review.data['meta.tags'] = [
            {'content': 'X' * 300, 'property': 'name', 'key': 'description'},
        ]
        validator.validate()
        expect(validator.add_violation.called).to_be_false()


    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = MetaTagsValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(2)
        expect('absent.metatags' in definitions).to_be_true()
        expect('page.metatags.description_too_big' in definitions).to_be_true()

        violation_defs = validator.get_violation_definitions()

        absent_metatags_desc = violation_defs['absent.metatags']['description']
        expect(absent_metatags_desc(None)).to_equal(
            "No meta tags found on this page. This is damaging for "
            "Search Engines."
        )

        metadesc_too_big_desc = violation_defs['page.metatags.description_too_big']['description']
        expect(metadesc_too_big_desc({'max_size': 300})).to_equal(
            "The meta description tag is longer than 300 characters. "
            "It is best to keep meta descriptions shorter for better "
            "indexing on Search engines."
        )
