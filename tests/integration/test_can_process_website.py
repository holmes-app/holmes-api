#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4

from preggy import expect
from tornado.testing import AsyncTestCase
from motorengine import connect

from holmes.reviewer import Reviewer
from holmes.models.review import Review
from holmes.models.page import Page
from holmes.models.domain import Domain
from holmes.config import Config
from holmes.validators.total_requests import TotalRequestsValidator
from holmes.validators.js_requests import JSRequestsValidator
from holmes.validators.css_requests import CSSRequestsValidator
from holmes.validators.link_crawler import LinkCrawlerValidator
from holmes.validators.img_requests import ImageRequestsValidator
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class CanProcessWebsiteTest(AsyncTestCase):
    def setUp(self):
        super(CanProcessWebsiteTest, self).setUp()
        connect('holmes', host='localhost', port=6685, io_loop=self.io_loop)

    def get_config(self):
        conf = {}
        conf['MAX_JS_REQUESTS_PER_PAGE'] = 0
        conf['MAX_JS_KB_PER_PAGE_AFTER_GZIP'] = 0
        conf['MAX_CSS_REQUESTS_PER_PAGE'] = 0
        conf['MAX_CSS_KB_PER_PAGE_AFTER_GZIP'] = 0

        return conf

    def get_reviewer(
            self, api_url=None, page_uuid=None, page_url="http://page.url",
            review_uuid=None, config=None, validators=None):

        if api_url is None:
            api_url = self.get_url('/')

        if page_uuid is None:
            page_uuid = str(uuid4())

        if review_uuid is None:
            review_uuid = uuid4()

        if config is None:
            config = Config(**self.get_config())

        if validators is None:
            validators = [
                TotalRequestsValidator,
                JSRequestsValidator,
                CSSRequestsValidator,
                LinkCrawlerValidator,
                ImageRequestsValidator,
            ]

        return Reviewer(
            api_url=api_url,
            page_uuid=str(page_uuid),
            page_url=page_url,
            review_uuid=str(review_uuid),
            config=config,
            validators=validators
        )

    def test_can_process_globo_com(self):
        Review.objects.delete(callback=self.stop)
        self.wait()
        Page.objects.delete(callback=self.stop)
        self.wait()
        Domain.objects.delete(callback=self.stop)
        self.wait()

        DomainFactory.create(name="globo.com", url="http://www.globo.com", callback=self.stop)
        domain = self.wait()

        PageFactory.create(domain=domain, url="http://www.globo.com/", callback=self.stop)
        page = self.wait()

        ReviewFactory.create(page=page, callback=self.stop)
        review = self.wait()

        reviewer = self.get_reviewer(
            api_url="http://localhost:2368",
            page_uuid=page.uuid,
            page_url="http://www.globo.com/",
            review_uuid=review.uuid
        )

        reviewer.review()

        Review.objects.get(review._id, callback=self.stop)
        loaded_review = self.wait(timeout=30)

        expect(loaded_review.facts).to_length(10)
        expect(loaded_review.violations).to_length(5)

        print
        print
        msg = 'Evaluation for "http://www.globo.com"'
        print msg
        print '=' * len(msg)

        print
        print 'Facts'
        print '-----'
        for fact in loaded_review.facts:
            print str(fact)

        print
        print 'Violations'
        print '----------'
        for violation in loaded_review.violations:
            print str(violation)

        print
        print
