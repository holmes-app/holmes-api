#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from tests.unit.base import ValidatorTestCase
from holmes.reviewer import Reviewer
from holmes.validators.image_alt import ImageAltValidator
from tests.fixtures import PageFactory


class TestImageAltValidator(ValidatorTestCase):

    def test_can_validate_image_without_alt_attribute(self):
        config = Config()
        config.MAX_IMAGE_ALT_SIZE = 70

        page = PageFactory.create(url='http://my-site.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
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
        validator = ImageAltValidator(reviewer)

        validator.add_violation = Mock()
        validator.review.data = {
            'page.all_images': [{
                'src': 'the-src'
            }]
        }
        validator.validate()
        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='invalid.images.alt',
                value=[('http://my-site.com/the-src', 'the-src')],
                points=20
            ))

        validator.add_violation = Mock()
        big_alt = 'x' * 71
        validator.review.data = {
            'page.all_images': [{
                'src': 'the-src',
                'alt': big_alt  # 71 characters string
            }]
        }
        validator.validate()
        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='invalid.images.alt_too_big',
                value={
                    'images': [
                        ('http://my-site.com/the-src', 'the-src', big_alt)
                    ],
                    'max_size': 70
                },
                points=20
            ))

        validator.add_violation = Mock()
        validator.review.data = {
            'page.all_images': [{}]
        }
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = ImageAltValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(2)
        expect('invalid.images.alt' in definitions).to_be_true()
        expect('invalid.images.alt_too_big' in definitions).to_be_true()

        data = [('http://my-site.com/the-src', 'the-src')]
        without_alt_def = definitions['invalid.images.alt']
        expect(without_alt_def['description'] % without_alt_def['value_parser'](data)).to_equal(
            'Images without alt text are not good for Search Engines. Images '
            'without alt were found for: <a href="http://my-site.com/the-src" '
            'target="_blank">the-src</a>.'
        )

        data = {
            'max_size': 70,
            'images': [('http://my-site.com/the-src', 'the-src', 'Abcdef')]
        }
        alt_too_big_def = definitions['invalid.images.alt_too_big']
        expect(alt_too_big_def['description'] % alt_too_big_def['value_parser'](data)).to_equal(
            'Images with alt text bigger than 70 chars are not good for '
            'search engines. Images with a too big alt were found for: '
            '<a href="http://my-site.com/the-src" alt="Abcdef" '
            'target="_blank">the-src</a>.'
        )
