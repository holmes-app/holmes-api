#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.head import HeadFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestHeadFacter(FacterTestCase):


    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<html><head><link rel="canonical" href="http://my-url.com?item=test" /></head></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content)
        reviewer.content_loaded(page.url, response)

        facter = HeadFacter(reviewer)
        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.review.data).to_include('page.head')
        head = facter.review.data['page.head'][0]
        expect(head.tag).to_equal('head')
        data = [('rel', 'canonical'), ('href', 'http://my-url.com?item=test')]
        expect(head.getchildren()[0].items()).to_equal(data)

        expect(facter.add_fact.called).to_be_false()

    def test_can_get_facts_without_head(self):
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
        response = Mock(status_code=200, text=content)
        reviewer.content_loaded(page.url, response)

        facter = HeadFacter(reviewer)

        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.add_fact.called).to_be_false()
        expect(facter.review.data).to_be_like({})
