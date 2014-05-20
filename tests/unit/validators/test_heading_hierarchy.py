#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.heading_hierarchy import (
    HeadingHierarchyValidator, H1HeadingValidator
)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestHeadingHierarchyValidator(ValidatorTestCase):

    def test_can_validate_heading_hierarchy(self):
        page = PageFactory.create()
        config = Config()
        config.MAX_HEADING_HIEARARCHY_SIZE = 150

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
        validator = HeadingHierarchyValidator(reviewer)

        # expecting no call of add_violation method
        validator.add_violation = Mock()
        validator.review.data = {
            'page.heading_hierarchy': [
                ('h1', 'Loren ipsum dolor sit amet'),
            ]
        }
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

        # expecting calling add_violation for `page.heading_hierarchy.size`
        validator.add_violation = Mock()
        hh_list = [
            ('h1', 'Loren ipsum dolor sit amet' * 10),
            ('h1', 'Loren ipsum dolor sit amet' * 10),
        ]
        validator.review.data = {'page.heading_hierarchy': hh_list}
        validator.validate()
        expect(validator.add_violation.called).to_be_true()
        validator.add_violation.assert_called_once_with(
            key='page.heading_hierarchy.size',
            value={
                'max_size': 150, 'hh_list': hh_list,
            },
            points=40
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = HeadingHierarchyValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)

        expect('page.heading_hierarchy.size' in definitions).to_be_true()
        definitions_value = definitions['page.heading_hierarchy.size']
        expect('title' in definitions_value).to_be_true()
        expect('description' in definitions_value).to_be_true()
        expect('category' in definitions_value).to_be_true()

        value = {
            'hh_list': [
                ('h1', 'Loren ipsum dolor sit amet'),
            ],
            'max_size': 150
        }
        violation_description = validator.get_violation_description(value)
        expect(violation_description).to_equal(
            'Heading hierarchy values bigger than 150 characters aren\'t good '
            'for Search Engines. This elements were found:'
            '<ul class="violation-hh-list"><li>'
            '<span class="hh-type">h1</span>: '
            'Loren ipsum dolor sit amet</li></ul>'
        )


class TestH1HeadingValidator(ValidatorTestCase):

    def test_can_validate_h1_headings(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
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
        validator = H1HeadingValidator(reviewer)

        # expecting no call of add_violation method
        validator.add_violation = Mock()
        validator.review.data = {
            'page.heading_hierarchy': [
                ('h1', 'Loren ipsum dolor sit amet'),
            ]
        }
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

        # expecting calling add_violation for
        # 'page.heading_hierarchy.h1_not_found'
        validator.add_violation = Mock()
        hh_list = [
            ('h2', 'Loren ipsum dolor sit amet'),
            ('h3', 'Loren ipsum dolor sit amet'),
        ]
        validator.review.data = {'page.heading_hierarchy': hh_list}
        validator.validate()
        expect(validator.add_violation.called).to_be_true()
        validator.add_violation.assert_called_once_with(
            key='page.heading_hierarchy.h1_not_found',
            value=None,
            points=30
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = H1HeadingValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(1)

        expect('page.heading_hierarchy.h1_not_found' in definitions).to_be_true()
        definitions_value = definitions['page.heading_hierarchy.h1_not_found']
        expect('title' in definitions_value).to_be_true()
        expect('description' in definitions_value).to_be_true()
        expect('category' in definitions_value).to_be_true()

        violation_description = validator.get_violation_description()
        expect(violation_description).to_equal(
            'Your page does not contain any H1 headings. H1 headings help '
            'indicate the important topics of your page to search engines. '
            'While less important than good meta-titles and descriptions, '
            'H1 headings may still help define the topic of your page to '
            'search engines.'
        )
