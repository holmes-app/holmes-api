#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.img_requests import ImageRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestImageRequestsValidator(ValidatorTestCase):

    def test_can_validate_image_requests_on_globo_html(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageRequestsValidator(reviewer)

        image = {
            'url': 'some_image.jpg',
            'status': 200,
            'content': self.get_file('2x2.png'),
            'html': None
        }
        validator.get_response = Mock(return_value=image)
        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_fact.call_args_list).to_length(2)
        expect(validator.add_fact.call_args_list[0]).to_equal(
            call(key='total.requests.img',
                 value=60,
                 title='Total images requests'))

        expect(validator.add_fact.call_args_list[1]).to_equal(
            call(key='total.size.img',
                 value=374.73046875,
                 unit='kb',
                 title='Total images size'))

        expect(validator.add_violation.call_args_list).to_include(
            call(key='total.requests.img',
                 title='Too many image requests.',
                 description='This page has 60 image requests (10 over limit). '
                             'Having too many requests impose a tax in the browser due to handshakes.',
                 points=50))

        expect(validator.add_violation.call_args_list).to_include(
            call(key='single.size.img',
                 title='Single image size in kb is too big.',
                 description='Found a image bigger then limit 6 (0 over limit): some_image.jpg',
                 points=0.57421875))

        expect(validator.add_violation.call_args_list).to_include(
            call(key='total.requests.img',
                 title='Too many image requests.',
                 description='This page has 60 image requests (10 over limit). '
                             'Having too many requests impose a tax in the browser due to handshakes.',
                 points=50))

    def test_can_validate_image_404(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = "<html><img src='/some_image.jpg'/></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageRequestsValidator(reviewer)

        image = {
            'url': '/some_image.jpg',
            'status': 404,
            'content': None,
            'html': None
        }
        validator.get_response = Mock(return_value=image)
        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(key='broken.img',
                 title='Image not found.',
                 description="The image in 'http://globo.com/some_image.jpg' "
                             "could not be found or took more than 10 seconds to load.",
                 points=50))

    def test_can_validate_single_image_html(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = "<html><img src='/some_image.jpg'/></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageRequestsValidator(reviewer)

        image = {
            'url': '/some_image.jpg',
            'status': 200,
            'content': self.get_file('1x1.png'),
            'html': None
        }
        validator.get_response = Mock(return_value=image)
        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

        expect(validator.add_fact.call_args_list).to_length(2)
        expect(validator.add_fact.call_args_list[0]).to_equal(
            call(key='total.requests.img',
                 value=1,
                 title='Total images requests'))

        expect(validator.add_fact.call_args_list[1]).to_equal(
            call(key='total.size.img',
                 value=0.12109375,
                 unit='kb',
                 title='Total images size'))

    def test_can_validate_html_without_images(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = "<html></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

        expect(validator.add_fact.call_args_list).to_length(2)
        expect(validator.add_fact.call_args_list[0]).to_equal(
            call(key='total.requests.img',
                 value=0,
                 title='Total images requests'))

        expect(validator.add_fact.call_args_list[1]).to_equal(
            call(key='total.size.img',
                 value=0.0,
                 unit='kb',
                 title='Total images size'))

    def test_can_validate_without_img_src(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = "<html><img src=''/></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageRequestsValidator(reviewer)

        validator.add_fact = Mock()
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

        expect(validator.add_fact.call_args_list).to_length(2)
        expect(validator.add_fact.call_args_list[0]).to_equal(
            call(key='total.requests.img',
                 value=1,
                 title='Total images requests'))

        expect(validator.add_fact.call_args_list[1]).to_equal(
            call(key='total.size.img',
                 value=0.0,
                 unit='kb',
                 title='Total images size'))
