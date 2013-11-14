#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.base import Validator
from tests.fixtures import PageFactory, ReviewFactory
from tests.unit.base import ApiTestCase


class TestBaseValidator(ApiTestCase):
    def test_can_validate(self):
        expect(Validator(None).validate()).to_be_true()

    def test_can_get_response(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).get_response('some url')
        mock_reviewer.get_response.assert_called_once_with('some url')

    def test_can_get_raw_response(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).get_raw_response('some url')
        mock_reviewer.raw_responses.get.assert_called_once_with('some url', None)

    def test_can_add_fact(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).add_fact('test', 10, 'title', 'unit')
        mock_reviewer.add_fact.assert_called_once_with('test', 10, 'title', 'unit')

    def test_can_add_violation(self):
        mock_reviewer = Mock()
        Validator(mock_reviewer).add_violation('test', 'title', 'description', 100)
        mock_reviewer.add_violation.assert_called_once_with('test', 'title', 'description', 100)

    def test_can_return_reviewer_info(self):
        review = ReviewFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=review.page.uuid,
            page_url=review.page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )

        validator = Validator(reviewer)

        expect(validator.page_uuid).to_equal(review.page.uuid)
        expect(validator.page_url).to_equal(review.page.url)
        expect(validator.review_uuid).to_equal(review.uuid)
        expect(validator.config).to_equal(reviewer.config)

    def test_is_absolute(self):
        validator = Validator(None)
        expect(validator.is_absolute('http://globoi.com/index.html')).to_be_true()

    def test_is_relative(self):
        validator = Validator(None)
        expect(validator.is_absolute('/index.html')).to_be_false()

    def test_can_rebase(self):
        page = PageFactory.create(url='http://globoi.com/test/index.html')
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )

        validator = Validator(reviewer)

        expect(validator.rebase('index.png')).to_equal('http://globoi.com/test/index.png')
        expect(validator.rebase('/index.png')).to_equal('http://globoi.com/index.png')

    def test_will_call_reviewer_enqueue(self):
        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )
        reviewer.enqueue = Mock()

        validator = Validator(reviewer)
        validator.enqueue('/')

        reviewer.enqueue.assert_called_once_with('/')

    def test_will_call_reviewer_add_fact(self):
        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )
        reviewer.add_fact = Mock()

        validator = Validator(reviewer)
        validator.add_fact('random.fact', 'random', 'value', 'title')
        reviewer.add_fact.assert_called_once_with('random.fact', 'random', 'value', 'title')

    def test_will_call_reviewer_add_violation(self):
        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )
        reviewer.add_violation = Mock()

        validator = Validator(reviewer)
        validator.add_violation('random.violation', 'random', 'violation', 0)
        reviewer.add_violation.assert_called_once_with('random.violation', 'random', 'violation', 0)

    def test_will_call_reviewer_get_status_code(self):
        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
            validators=[]
        )
        reviewer.get_status_code = Mock()

        validator = Validator(reviewer)
        validator.get_status_code('http://globo.com')
        reviewer.get_status_code.assert_called_once_with('http://globo.com')

    def test_can_encode_content(self):
        validator = Validator(None)
        content = u'random content'
        gziped_content = validator.to_gzip(content)

        expect(content).to_equal(gziped_content.decode('zip'))
