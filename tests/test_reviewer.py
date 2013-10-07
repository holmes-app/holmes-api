#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4

from preggy import expect
import lxml.html

from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.config import Config
from holmes.validators.base import Validator
from tests.base import ApiTestCase


class TestReview(ApiTestCase):
    def test_can_create_reviewer(self):
        page_uuid = uuid4()
        page_url = "http://page.url"
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]

        reviewer = Reviewer(
            page_uuid=str(page_uuid),
            page_url=page_url,
            review_uuid=str(review_uuid),
            config=config,
            validators=validators
        )

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal(page_url)
        expect(reviewer.review_uuid).to_equal(review_uuid)
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_reviewer_fails_if_wrong_config(self):
        page_uuid = uuid4()
        page_url = "http://page.url"
        review_uuid = uuid4()
        config = "wrong config object"
        validators = [Validator]

        try:
            Reviewer(
                page_uuid=str(page_uuid),
                page_url=page_url,
                review_uuid=str(review_uuid),
                config=config,
                validators=validators
            )
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("config argument must be an instance of holmes.config.Config")
        else:
            assert False, "Shouldn't have gotten this far"

    def test_reviewer_fails_if_wrong_validators(self):
        page_uuid = uuid4()
        page_url = "http://page.url"
        review_uuid = uuid4()
        config = Config()
        validators = [Validator, "wtf"]
        validators2 = [Validator, Config]

        try:
            Reviewer(
                page_uuid=str(page_uuid),
                page_url=page_url,
                review_uuid=str(review_uuid),
                config=config,
                validators=validators
            )
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("All validators must subclass holmes.validators.base.Validator")
        else:
            assert False, "Shouldn't have gotten this far"

        try:
            Reviewer(
                page_uuid=str(page_uuid),
                page_url=page_url,
                review_uuid=str(review_uuid),
                config=config,
                validators=validators2
            )
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("All validators must subclass holmes.validators.base.Validator")
        else:
            assert False, "Shouldn't have gotten this far"

    def test_load_content_raises_when_invalid_status_code(self):
        page_uuid = uuid4()
        page_url = "http://page.url"
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]

        reviewer = Reviewer(
            page_uuid=str(page_uuid),
            page_url=page_url,
            review_uuid=str(review_uuid),
            config=config,
            validators=validators
        )

        reviewer.responses[page_url] = {
            'status': 500,
            'content': "",
            'html': None
        }

        try:
            reviewer.load_content()
        except InvalidReviewError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("Could not load 'http://page.url'!")
        else:
            assert False, "Should not have gotten this far"

    def test_get_response_fills_dict(self):
        page_uuid = uuid4()
        page_url = "http://www.google.com"
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]

        reviewer = Reviewer(
            page_uuid=str(page_uuid),
            page_url=page_url,
            review_uuid=str(review_uuid),
            config=config,
            validators=validators
        )

        reviewer.get_response(page_url)

        expect(reviewer.responses).to_include(page_url)
        expect(reviewer.responses[page_url]['status']).to_equal(200)
        expect(reviewer.responses[page_url]['content']).to_include("btnG")

        expect(reviewer.responses[page_url]['html']).not_to_be_null()
        expect(reviewer.responses[page_url]['html']).to_be_instance_of(lxml.html.HtmlElement)

    def test_review_calls_validators(self):
        test_class = {}

        class MockValidator(Validator):
            def validate(self):
                test_class['has_validated'] = True

        page_uuid = uuid4()
        page_url = "http://page.url"
        review_uuid = uuid4()
        config = Config()
        validators = [MockValidator]

        reviewer = Reviewer(
            page_uuid=str(page_uuid),
            page_url=page_url,
            review_uuid=str(review_uuid),
            config=config,
            validators=validators
        )

        reviewer.responses[page_url] = {
            'status': 200,
            'content': "<html><head></head><body></body></html>",
            'html': None
        }

        reviewer.review()

        expect(test_class['has_validated']).to_be_true()
