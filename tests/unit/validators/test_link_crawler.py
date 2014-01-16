#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.link_crawler import LinkCrawlerValidator
from tests.fixtures import PageFactory
from tests.unit.base import ValidatorTestCase


class TestLinkCrawlerValidator(ValidatorTestCase):

    def test_validate(self):
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

        reviewer.increase_lambda_tax = Mock()

        validator = LinkCrawlerValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.links': [
                ('http://g1.com/', Mock(status_code=404,
                                        effective_url='http://g1.com/')),
                ('http://g2.com/', Mock(status_code=302,
                                        effective_url='http://g2.com/')),
                ('http://g3.com/', Mock(status_code=307,
                                        effective_url='http://g3.com/'))
            ]
        }

        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='link.broken',
                value=set(['http://g1.com/']),
                points=100
            ))

        expect(validator.add_violation.call_args_list).to_include(
            call(
                key='link.moved.temporarily',
                value=set(['http://g2.com/', 'http://g3.com/']),
                points=100
            ))

    def test_validate_no_links(self):
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

        validator = LinkCrawlerValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.links': []
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = LinkCrawlerValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(2)
        expect('link.broken' in definitions).to_be_true()
        expect('link.moved.temporarily' in definitions).to_be_true()

        redirect_message = validator.get_redirect_message(
            set(['http://globo.com/'])
        )

        expect(redirect_message).to_equal(
            'A link from your page to "<a href="http://globo.com/" '
            'target="_blank">Link #0</a>" is using a 302 or 307 redirect. '
            'It passes 0% of link juice (ranking power) and, in most cases, '
            'should not be used. Use 301 instead.')

        broken_link_message = validator.get_broken_link_message(
            set(['http://globo.com/'])
        )

        expect(broken_link_message).to_equal(
            'This page contains broken links to <a href="http://globo.com/" '
            'target="_blank">Link #0</a> (the urls failed to load or '
            'timed-out after 10 seconds). This can lead your site to lose '
            'rating with Search Engines and is misleading to users.')
