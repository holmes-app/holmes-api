#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.last_modified import LastModifiedValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestLastModifiedValidator(ValidatorTestCase):

    def test_can_validate_last_modified(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = LastModifiedValidator(reviewer)
        validator.add_violation = Mock()

        validator.review.data = {
            'page.last_modified': None
        }

        validator.review.facts = {
            'page.last_modified': None
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.last_modified.not_found',
            value=page.url,
            points=50
        )

    def test_can_validate_with_headers(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        validator = LastModifiedValidator(reviewer)
        validator.add_violation = Mock()

        validator.review.data = {
            'page.last_modified': datetime.datetime(2014, 1, 13, 1, 16, 10)
        }

        validator.review.facts = {
            'page.last_modified': datetime.datetime(2014, 1, 13, 1, 16, 10)
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LastModifiedValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('page.last_modified.not_found' in definitions).to_be_true()
