#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
from tornado.testing import gen_test

from holmes.validators.base import Validator
from tests.unit.base import ApiTestCase


class TestBaseValidator(ApiTestCase):
    @gen_test
    def test_can_validate(self):
        expect(Validator(None).validate()).to_be_true()

    def test_can_get_response(self):
        mock_reviewer = Mock()

        Validator(mock_reviewer).get_response("some url")

        mock_reviewer.get_response.assert_called_once_with('some url')

    @gen_test
    def test_can_add_fact(self):
        mock_reviewer = Mock()

        Validator(mock_reviewer).add_fact('test', 10, 'unit')

        mock_reviewer.add_fact.assert_called_once_with('test', 10, 'unit')

    @gen_test
    def test_can_add_violation(self):
        mock_reviewer = Mock()

        Validator(mock_reviewer).add_violation('test', 'title', 'description', 100)

        mock_reviewer.add_violation.assert_called_once_with('test', 'title', 'description', 100)
