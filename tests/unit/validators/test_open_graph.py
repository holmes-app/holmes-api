#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.validators.open_graph import OpenGraphValidator
from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase
from holmes.config import Config
from holmes.reviewer import Reviewer


class TestOpenGraphValidator(ValidatorTestCase):

    def test_can_validate(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html><meta charset="UTF-8"></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = OpenGraphValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [{'key': 'meta', 'content': 'utf-8', 'property': ''}],
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                points=200,
                key='absent.metatags.open_graph',
                value=['og:title', 'og:type', 'og:image', 'og:url']
            ))

    def test_can_validate_without_meta_tags(self):
        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = OpenGraphValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = OpenGraphValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('absent.metatags.open_graph' in definitions).to_be_true()

        og_message = validator.get_open_graph_message(['og:type'])
        expect(og_message).to_equal('Some tags are missing: og:type')

    def test_can_validate_og_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html>' \
            '<meta property="og:title" content="Metal" />' \
            '<meta property="og:type" content="video.movie" />' \
            '<meta property="og:url" content="http://a.com" />' \
            '<meta property="og:image" content="http://a.com/rock.png" />' \
            '</html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = OpenGraphValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [
                {
                    'key': 'og:title',
                    'content': 'Metal',
                    'property': 'property'
                }, {
                    'key': 'og:type',
                    'content': 'video.movie',
                    'property': 'property'
                }, {
                    'key': 'og:url',
                    'content': 'http://a.com',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/rock.png',
                    'property': 'property'
                }
            ],
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_multiple_og_image(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html>' \
            '<meta property="og:title" content="Metal" />' \
            '<meta property="og:type" content="video.movie" />' \
            '<meta property="og:url" content="http://a.com" />' \
            '<meta property="og:image" content="http://a.com/paper.png" />' \
            '<meta property="og:image" content="http://a.com/rock.png" />' \
            '<meta property="og:image" content="http://a.com/scissors.png" />' \
            '<meta property="og:image" content="http://a.com/lizard.png" />' \
            '<meta property="og:image" content="http://a.com/spock.png" />' \
            '</html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = OpenGraphValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'meta.tags': [
                {
                    'key': 'og:title',
                    'content': 'Metal',
                    'property': 'property'
                }, {
                    'key': 'og:type',
                    'content': 'video.movie',
                    'property': 'property'
                }, {
                    'key': 'og:url',
                    'content': 'http://a.com',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/paper.png',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/rock.png',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/scissors.png',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/lizard.png',
                    'property': 'property'
                }, {
                    'key': 'og:image',
                    'content': 'http://a.com/spock.png',
                    'property': 'property'
                }
            ],
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()
