#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Page
from tests.unit.base import ApiTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestPage(ApiTestCase):
    @gen_test
    def test_can_create_page(self):
        page = PageFactory.create()

        expect(page.uuid).not_to_be_null()
        expect(page.id).not_to_be_null()
        expect(page.url).to_include('http://my-site.com/')

        expect(page.created_date).to_be_like(datetime.now())
        expect(page.last_review_started_date).to_be_null()
        expect(page.last_review_date).to_be_null()

    def test_can_convert_page_to_dict(self):
        page = PageFactory.create()

        page_dict = page.to_dict()

        expect(page_dict['uuid']).to_equal(str(page.uuid))
        expect(page_dict['url']).to_equal(page.url)

    def test_can_get_violations_per_day(self):
        dt = datetime(1997, 10, 10, 10, 10, 10)
        dt2 = datetime(1997, 10, 11, 10, 10, 10)
        dt3 = datetime(1997, 10, 12, 10, 10, 10)

        page = PageFactory.create()

        ReviewFactory.create(page=page, domain=page.domain, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(page=page, domain=page.domain, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        ReviewFactory.create(page=page, domain=page.domain, is_active=True, is_complete=True, completed_date=dt3, number_of_violations=30)

        violations = page.get_violations_per_day(self.db)

        expect(violations["1997-10-10"]).to_be_like({
            "violation_count": 20,
            "violation_points": 190
        })

        expect(violations["1997-10-11"]).to_be_like({
            "violation_count": 10,
            "violation_points": 45
        })

        expect(violations["1997-10-12"]).to_be_like({
            "violation_count": 30,
            "violation_points": 435
        })

    def test_can_get_page_by_uuid(self):
        page = PageFactory.create()
        PageFactory.create()

        loaded_page = Page.by_uuid(page.uuid, self.db)
        expect(loaded_page.id).to_equal(page.id)

        invalid_page = Page.by_uuid(uuid4(), self.db)
        expect(invalid_page).to_be_null()
