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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
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

        reviewer.violation_definitions = {
            'single.size.img': {'default_value': 6},
            'total.requests.img': {'default_value': 50},
            'total.size.img': {'default_value': 100},
        }

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
        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'single.size.img': {'default_value': 6},
            'total.requests.img': {'default_value': 50},
            'total.size.img': {'default_value': 100},
        }

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
        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'single.size.img': {'default_value': 6},
            'total.requests.img': {'default_value': 50},
            'total.size.img': {'default_value': 100},
        }

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
        page = PageFactory.create(url="http://globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
        )

        reviewer.violation_definitions = {
            'single.size.img': {'default_value': 6},
            'total.requests.img': {'default_value': 50},
            'total.size.img': {'default_value': 100},
        }

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

        expect(definitions).to_length(4)
        expect('broken.img' in definitions).to_be_true()
        expect('single.size.img' in definitions).to_be_true()
        expect('total.requests.img' in definitions).to_be_true()
        expect('total.size.img' in definitions).to_be_true()

        val = set(['http://globo.com/some_image.jpg'])
        expect(validator.get_broken_images_parsed_values(val)).to_equal({
            'images': (
                '<a href="http://globo.com/some_image.jpg" '
                'target="_blank">Link #0</a>')
        })

        single_image_size_parsed_value = validator.get_single_image_size_parsed_value(
            {'over_max_size': [('http://a.com', 100), ('http://b.com', 30)],
             'limit': 20}
        )
        expect(single_image_size_parsed_value).to_equal({
            'limit': 20,
            'images': (
                '<a href="http://a.com" target="_blank">a.com</a> (100kb)'
                ', <a href="http://b.com" target="_blank">b.com</a> (30kb)'
            )
        })

    def test_can_get_default_violations_values(self):
        config = Config()
        config.MAX_KB_SINGLE_IMAGE = 70
        config.MAX_IMG_REQUESTS_PER_PAGE = 10
        config.MAX_IMG_KB_PER_PAGE = 5

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = ImageRequestsValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('single.size.img')
        expect(violations_values).to_include('total.size.img')
        expect(violations_values).to_include('total.requests.img')

        expect(violations_values['single.size.img']).to_length(2)
        expect(violations_values['total.size.img']).to_length(2)
        expect(violations_values['total.requests.img']).to_length(2)

        expect(violations_values['single.size.img']).to_be_like({
            'value': config.MAX_KB_SINGLE_IMAGE,
            'description': config.get_description('MAX_KB_SINGLE_IMAGE')
        })

        expect(violations_values['total.size.img']).to_be_like({
            'value': config.MAX_IMG_KB_PER_PAGE,
            'description': config.get_description('MAX_IMG_KB_PER_PAGE')
        })

        expect(violations_values['total.requests.img']).to_be_like({
            'value': config.MAX_IMG_REQUESTS_PER_PAGE,
            'description': config.get_description('MAX_IMG_REQUESTS_PER_PAGE')
        })
