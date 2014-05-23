#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.link_with_rel_canonical import (
    LinkWithRelCanonicalValidator
)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestLinkWithRelCanonicalValidator(ValidatorTestCase):

    def test_validate(self):
        config = Config()

        page = PageFactory.create(url='http://globo.com/1?item=test')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.meta.canonical',
                value=None,
                points=30
            ))

    def test_force_canonical(self):
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

        reviewer.violation_definitions = {
            'absent.meta.canonical': {'default_value': True},
        }

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='absent.meta.canonical',
                value=None,
                points=30
            ))

    def test_query_string_without_params(self):
        config = Config()
        config.FORCE_CANONICAL = False

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        content = '<html><head></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': [{}]}

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkWithRelCanonicalValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)
        expect('absent.meta.canonical' in definitions).to_be_true()

    def test_page_without_head_tag(self):
        config = Config()
        config.FORCE_CANONICAL = False

        page = PageFactory.create(url='http://globo.com/1?item=test')

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

        validator = LinkWithRelCanonicalValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {'page.head': None}

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_validate_page_with_invalid_url(self):
        page = PageFactory.create(url='http://[globo.com/1?item=test')

        try:
            Reviewer(
                api_url='http://localhost:2368',
                page_uuid=page.uuid,
                page_url=page.url,
                page_score=0.0,
                config=Config(),
                validators=[]
            )
        except ValueError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.message).to_equal('Invalid IPv6 URL')
            return
        else:
            assert False, 'Should not have got this far'

    def test_can_get_default_violations_values(self):
        config = Config()
        config.FORCE_CANONICAL = False

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = LinkWithRelCanonicalValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('absent.meta.canonical')

        expect(violations_values['absent.meta.canonical']).to_length(2)

        expect(violations_values['absent.meta.canonical']).to_be_like({
            'value': config.FORCE_CANONICAL,
            'description': config.get_description('FORCE_CANONICAL')
        })
