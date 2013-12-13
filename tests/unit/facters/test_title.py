#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.title import TitleFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestTitleFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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
        reviewer.content_loaded(page.url, Mock(status_code=200, text=content, headers={}))

        facter = TitleFacter(reviewer)
        facter.add_fact = Mock()

        facter.get_facts()

        facter.add_fact.assert_called_once_with(
            key='page.title',
            value=u'globo.com - Absolutamente tudo sobre not\xedcias, '
                  'esportes e entretenimento',
        )

        expect(facter.review.data).to_include('page.title_count')
        expect(facter.review.data['page.title_count']).to_equal(1)

    def test_no_title_tag(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        reviewer.content_loaded(page.url, Mock(status_code=200, text=content, headers={}))

        facter = TitleFacter(reviewer)
        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.add_fact.called).to_be_false()
        expect(facter.review.data).to_be_like({})

    def test_can_get_fact_definitions(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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

        facter = TitleFacter(reviewer)

        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(1)
        expect('page.title' in definitions).to_be_true()
