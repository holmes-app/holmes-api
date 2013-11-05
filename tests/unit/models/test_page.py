#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestPage(ApiTestCase):
    @gen_test
    def test_can_create_page(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        expect(page.uuid).not_to_be_null()
        expect(page._id).not_to_be_null()
        expect(page.url).to_include('http://my-site.com/')
        expect(page.title).to_include('page-')

        expect(page.added_date).to_be_like(datetime.now())
        expect(page.updated_date).to_be_like(datetime.now())

    @gen_test
    def test_can_convert_page_to_dict(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        page_dict = page.to_dict()

        expect(page_dict['uuid']).to_equal(str(page.uuid))
        expect(page_dict['title']).to_equal(page.title)
        expect(page_dict['url']).to_equal(page.url)

    @gen_test
    def test_can_get_violations_per_day(self):
        dt = datetime(2013, 10, 10, 10, 10, 10)
        dt2 = datetime(2013, 10, 11, 10, 10, 10)
        dt3 = datetime(2013, 10, 12, 10, 10, 10)

        domain = yield DomainFactory.create()

        page = yield PageFactory.create(domain=domain)

        yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        yield ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt3, number_of_violations=30)

        violations = yield page.get_violations_per_day()

        expect(violations["2013-10-10"]).to_be_like({
            "violation_count": 20,
            "violation_points": 190
        })

        expect(violations["2013-10-11"]).to_be_like({
            "violation_count": 10,
            "violation_points": 45
        })

        expect(violations["2013-10-12"]).to_be_like({
            "violation_count": 30,
            "violation_points": 435
        })
