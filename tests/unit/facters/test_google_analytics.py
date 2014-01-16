#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.google_analytics import GoogleAnalyticsFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestGoogleAnalyticsFacter(FacterTestCase):

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

        content = self.get_file('globo.html')

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

        facter = GoogleAnalyticsFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(1)
        expect(facter.review.data).to_include('page.google_analytics')

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.google_analytics',
                value=set([
                    ('UA-296593-2', 'www.globo.com'),
                    ('UA-296593-15', '.globo.com')
                ])
            ))

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = GoogleAnalyticsFacter(reviewer)

        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(1)
        expect('page.google_analytics' in definitions).to_be_true()
