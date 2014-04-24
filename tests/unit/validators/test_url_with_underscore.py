#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect

from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase
from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.url_with_underscore import UrlWithUnderscoreValidator


class TestUrlWithUnderscoreValidator(ValidatorTestCase):

    def test_can_validate_url_with_underscore(self):
        page = PageFactory.create(url='http://globo.com/test_underscore')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = UrlWithUnderscoreValidator(reviewer)
        validator.add_violation = Mock()
        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='invalid.url_word_separator',
            value=page.url,
            points=10
        )

    def test_can_validate_url_without_underscore(self):
        page = PageFactory.create(url='http://globo.com/test-underscore')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = UrlWithUnderscoreValidator(reviewer)
        validator.add_violation = Mock()
        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = UrlWithUnderscoreValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)

        expect('invalid.url_word_separator' in definitions).to_be_true()

        expect(validator.get_url_with_underscore_message()).to_equal(
            'Google treats a hyphen as a word separator, but does '
            'not treat an underscore that way. Google treats and '
            'underscore as a word joiner — so red_sneakers is the '
            'same as redsneakers to Google. This has been confirmed '
            'directly by Google themselves, including the fact that '
            'using dashes over underscores will have a (minor) '
            'ranking benefit.'
        )
