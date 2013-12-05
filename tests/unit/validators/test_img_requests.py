#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.img_requests import ImageRequestsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestImageRequestsValidator(ValidatorTestCase):

    def test_can_validate_image_requests_on_globo_html(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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
        validator.add_violation = Mock()
        validator.review.data = {
            'page.images': [
                (
                    'some_image.jpg',
                    Mock(status_code=200, text=self.get_file('2x2.png'))
                ) for i in xrange(60)
            ],
            'total.size.img': 106,
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='total.requests.img',
                value={'total': 60, 'limit': 10},
                points=50
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='single.size.img',
                value={
                    'limit': 6,
                    'over_max_size': set([('some_image.jpg', 6.57421875)])
                },
                points=0.57421875
            ))

    def test_can_validate_image_404(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        validator = ImageRequestsValidator(reviewer)
        validator.add_violation = Mock()

        img_url = 'http://globo.com/some_image.jpg'
        validator.review.data = {
            'page.images': [
                (img_url, Mock(status_code=404, text=None))
            ],
            'total.size.img': 60,
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='broken.img',
                value=set(['http://globo.com/some_image.jpg']),
                points=50
            ))

    def test_can_validate_single_image_html(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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
        validator.add_violation = Mock()
        validator.review.data = {
            'page.images': [
                ('http://globo.com/some_image.jpg', Mock(status_code=200, text='bla'))
            ],
            'total.size.img': 60,
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_html_without_images(self):
        config = Config()
        config.MAX_IMG_REQUESTS_PER_PAGE = 50
        config.MAX_KB_SINGLE_IMAGE = 6
        config.MAX_IMG_KB_PER_PAGE = 100

        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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

        validator.add_violation = Mock()
        validator.review.data = {
            'page.images': [],
            'total.size.img': 60,
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = ImageRequestsValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect('broken.img' in definitions).to_be_true()
        expect('single.size.img' in definitions).to_be_true()
        expect('total.requests.img' in definitions).to_be_true()
        expect('total.size.img' in definitions).to_be_true()

        broken_images_message = validator.get_broken_images_message(
            set(['http://globo.com/some_image.jpg'])
        )
        requests_images_message = validator.get_requests_images_message(
            {'total': 60, 'limit': 10}
        )
        total_size_message = validator.get_total_size_message(60)

        expect(broken_images_message).to_equal(
            'The image(s) in "<a href="http://globo.com/some_image.jpg" '
            'target="_blank">Link #0</a>" could not be found or took '
            'more than 10 seconds to load.')

        expect(requests_images_message).to_equal(
            'This page has 60 image requests (10 over limit). Having too many '
            'requests impose a tax in the browser due to handshakes.'
        )

        expect(total_size_message).to_equal(
            'There`s 60.00kb of images in this page and that adds up to more '
            'download time slowing down the page rendering to the user.'
        )
