#!/usr/bin/python
# -*- coding: utf-8 -*-

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
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'page.metatags.description_too_big': {'default_value': 300},
        }

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

    def test_can_get_default_violations_values(self):
        config = Config()
        config.METATAG_DESCRIPTION_MAX_SIZE = 300

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = MetaTagsValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('page.metatags.description_too_big')

        expect(violations_values['page.metatags.description_too_big']).to_length(2)

        expect(violations_values['page.metatags.description_too_big']).to_be_like({
            'value': config.METATAG_DESCRIPTION_MAX_SIZE,
            'description': config.get_description('METATAG_DESCRIPTION_MAX_SIZE')
        })
