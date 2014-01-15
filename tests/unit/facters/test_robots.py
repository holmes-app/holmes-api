#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.robots import RobotsFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestRobotsFacter(FacterTestCase):

    def test_get_facts_cant_run_if_page_is_not_root(self):
        page = PageFactory.create(url="http://www.globo.com/index.html")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        facter = RobotsFacter(reviewer)
        facter.add_fact = Mock()
        facter.async_get = Mock()

        facter.get_facts()

        expect(facter.add_fact.call_count).to_equal(0)
        expect(facter.async_get.call_count).to_equal(0)

    def test_get_robots_from_root_domain(self):
        page = PageFactory.create(url="http://www.globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        facter = RobotsFacter(reviewer)
        facter.async_get = Mock()
        facter.add_fact = Mock()
        facter.get_facts()

        robots_url = 'http://www.globo.com/robots.txt'

        expect(facter.review.data).to_length(1)
        expect(facter.review.data['robots.response']).to_equal(None)

        facter.async_get.assert_called_once_with(
            robots_url,
            facter.handle_robots_loaded
        )

        response = Mock(status_code=200, text='', headers={})
        facter.handle_robots_loaded(robots_url, response)

        expect(facter.review.data['robots.response']).to_equal(response)

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='robots.url',
                value=robots_url,
            ))

    def test_handle_robots_loaded_should_save_data(self):
        page = PageFactory.create(url="http://www.globo.com")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        facter = RobotsFacter(reviewer)
        response = Mock(status_code=200)
        facter.review.data['robots.response'] = None
        facter.handle_robots_loaded(
            'http://www.globo.com/robots.txt',
            response
        )

        expect(facter.review.data['robots.response']).to_equal(response)

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = RobotsFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(1)
        expect('robots.url' in definitions).to_be_true()
