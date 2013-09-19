#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test

from holmes.validators.base import Validator
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestBaseValidator(ApiTestCase):
    @gen_test
    def test_can_validate(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        result = Validator(None, review).validate()

        expect(review.violations).to_be_empty()
        expect(review.facts).to_be_empty()
        expect(result).to_be_true()
