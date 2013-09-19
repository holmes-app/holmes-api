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

    @gen_test
    def test_can_add_fact(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        Validator(None, review).add_fact('test', 10)
        Validator(None, review).add_fact('other', 20, 'unit')

        expect(review.facts).to_length(2)

        expect(review.facts[0].key).to_equal('test')
        expect(review.facts[0].value).to_equal(10)
        expect(review.facts[0].unit).to_equal('value')

        expect(review.facts[1].key).to_equal('other')
        expect(review.facts[1].value).to_equal(20)
        expect(review.facts[1].unit).to_equal('unit')
