#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

from preggy import expect

from holmes.config import Config
from holmes.models import Page
from tests.unit.base import ApiTestCase
from tests.fixtures import PageFactory, ReviewFactory, DomainFactory


class TestPage(ApiTestCase):
    @property
    def sync_cache(self):
        return self.connect_to_sync_redis()

    def test_can_create_page(self):
        page = PageFactory.create()

        expect(page.uuid).not_to_be_null()
        expect(page.id).not_to_be_null()
        expect(page.url).to_include('http://my-site.com/')

        expect(page.created_date).to_be_like(datetime.utcnow())
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

        expect(violations).to_be_like([
            {
                "completedAt": "1997-10-10",
                "violation_count": 20,
                "violation_points": 190
            },
            {
                "completedAt": "1997-10-11",
                "violation_count": 10,
                "violation_points": 45
            },
            {
                "completedAt": "1997-10-12",
                "violation_count": 30,
                "violation_points": 435
            }
        ])

    def test_can_get_page_by_uuid(self):
        page = PageFactory.create()
        PageFactory.create()

        loaded_page = Page.by_uuid(page.uuid, self.db)
        expect(loaded_page.id).to_equal(page.id)

        invalid_page = Page.by_uuid(uuid4(), self.db)
        expect(invalid_page).to_be_null()

    def test_can_get_page_by_url_hash(self):
        page = PageFactory.create()
        PageFactory.create()

        loaded_page = Page.by_url_hash(page.url_hash, self.db)
        expect(loaded_page.id).to_equal(page.id)

        invalid_page = Page.by_uuid('123', self.db)
        expect(invalid_page).to_be_null()

    def test_update_pages_score(self):
        config = Config()
        config.MAX_PAGE_SCORE = 15000000

        self.db.query(Page).delete()
        self.sync_cache.redis.delete('pages-score')

        page1 = PageFactory.create(score=3)
        page2 = PageFactory.create(score=0)

        for i in range(3):
            self.sync_cache.increment_page_score(page1.id)

        self.sync_cache.increment_page_score(page2.id)

        expect(page1.score).to_equal(3)
        expect(page2.score).to_equal(0)

        Page.update_pages_score(self.db, self.sync_cache, config)
        self.db.flush()

        self.db.refresh(page1)
        self.db.refresh(page2)

        expect(page1.score).to_equal(6)
        expect(page2.score).to_equal(1)
