#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.css import CSSFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestCSSFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<html><link href="a.css" /><link href="a.cse" /></html>'

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

        facter = CSSFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.css',
                value=set([]),
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.css',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.css.gzipped',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.requests.css',
                value=1,
            ))

        expect(facter.review.data).to_be_like({
            'total.size.css': 0,
            'total.size.css.gzipped': 0,
            'page.css': set([])
        })

        facter.async_get.assert_called_once_with(
            'http://my-site.com/a.css',
            facter.handle_url_loaded
        )

    def test_handle_url_loaded(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<html><link href="a.css" /></html>'

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

        facter = CSSFacter(reviewer)
        facter.async_get = Mock()
        facter.get_facts()

        facter.handle_url_loaded(page.url, response)

        expect(facter.review.data).to_include('total.size.css')
        expect(facter.review.data['total.size.css']).to_equal(0.033203125)

        expect(facter.review.data).to_include('total.size.css.gzipped')
        expect(facter.review.data['total.size.css.gzipped']).to_equal(0.0380859375)

        expect(facter.review.data).to_include('page.css')
        data = set([(page.url, response)])
        expect(facter.review.data['page.css']).to_equal(data)

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = CSSFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect('page.css' in definitions).to_be_true()
        expect('total.size.css' in definitions).to_be_true()
        expect('total.size.css.gzipped' in definitions).to_be_true()
        expect('total.requests.css' in definitions).to_be_true()
