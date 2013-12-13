#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.body import BodyFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestBodyFacter(FacterTestCase):


    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<html><body class="test"></body></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = BodyFacter(reviewer)
        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.review.data).to_include('page.body')
        expect(facter.review.data['page.body'][0].tag).to_equal('body')

        expect(facter.add_fact.called).to_be_false()

    def test_can_get_facts_without_body(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = "<html></html>"

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = BodyFacter(reviewer)

        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.add_fact.called).to_be_false()
        expect(facter.review.data).to_be_like({})

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = BodyFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(0)
        expect(definitions).to_equal({})
