#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.last_modified import LastModifiedFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestLastModifiedFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<html></html>'

        headers = {'Last-Modified': 'January 13, 2014 1:16:10 PM'}

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content),
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers=headers)
        reviewer.content_loaded(page.url, response)

        facter = LastModifiedFacter(reviewer)
        facter.add_fact = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(1)
        expect(facter.review.data).to_include('page.last_modified')

        expect(facter.review.data).to_be_like({
            'page.last_modified': datetime.datetime(2014, 1, 13, 1, 16, 10)}
        )

    def test_can_load_url_with_empy_headers(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content),
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = LastModifiedFacter(reviewer)
        facter.add_fact = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(0)
        expect(facter.review.data).to_be_like({})
        expect(facter.add_fact.called).to_be_false()

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = LastModifiedFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(1)
        expect('page.last_modified' in definitions).to_be_true()
