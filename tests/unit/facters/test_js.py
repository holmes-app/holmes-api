#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.js import JSFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestJSFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create(url='http://my-site.com/')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<script type="text/javascript" src="teste.js"></script>'

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

        facter = JSFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.js',
                value=set([]),
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=1,
            ))

        expect(facter.review.data).to_length(3)

        expect(facter.review.data).to_be_like({
            'total.size.js.gzipped': 0,
            'page.js': set([]),
            'total.size.js': 0
        })

        facter.async_get.assert_called_once_with(
            'http://my-site.com/teste.js',
            facter.handle_url_loaded
        )

    def test_handle_url_loaded(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<script type="text/javascript" src="teste.js"></script>'

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

        facter = JSFacter(reviewer)
        facter.async_get = Mock()
        facter.get_facts()

        facter.handle_url_loaded(page.url, response)

        expect(facter.review.data).to_include('total.size.js')
        expect(facter.review.data['total.size.js']).to_equal(0.0537109375)

        expect(facter.review.data).to_include('total.size.js.gzipped')
        expect(facter.review.data['total.size.js.gzipped']).to_equal(0.05078125)

        expect(facter.review.data).to_include('page.js')
        data = set([(page.url, response)])
        expect(facter.review.data['page.js']).to_equal(data)

    def test_handle_url_loaded_with_empty_content(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = ''
        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': content
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = JSFacter(reviewer)
        facter.async_get = Mock()
        facter.get_facts()

        facter.handle_url_loaded(page.url, response)

        expect(facter.review.data).to_include('total.size.js')
        expect(facter.review.data['total.size.js']).to_equal(0)

        expect(facter.review.data).to_include('total.size.js.gzipped')
        expect(facter.review.data['total.size.js.gzipped']).to_equal(0)

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = JSFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(4)
        expect('page.js' in definitions).to_be_true()
        expect('total.size.js' in definitions).to_be_true()
        expect('total.size.js.gzipped' in definitions).to_be_true()
        expect('total.requests.js' in definitions).to_be_true()

    def test_invalid_url(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<html><link href="http://].js" /></html>'

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

        facter = JSFacter(reviewer)
        facter.add_fact = Mock()
        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.js',
                value=set([]),
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0,
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=0,
            ))

        expect(facter.review.data).to_include('total.size.js')
        expect(facter.review.data['total.size.js']).to_equal(0)

        expect(facter.review.data).to_include('total.size.js.gzipped')
        expect(facter.review.data['total.size.js.gzipped']).to_equal(0)

        expect(facter.review.data).to_include('page.js')
        expect(facter.review.data['page.js']).to_equal(set([]))
