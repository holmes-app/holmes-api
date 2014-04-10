#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.heading_hierarchy import HeadingHierarchyValidator
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

        validator = HeadingHierarchyValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.heading_hierarchy': [
                ('h1', 'Loren ipsum dolor sit amet'),
            ]
        }
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

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
