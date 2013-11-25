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
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
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
        response = Mock(status_code=200, text=content)
        reviewer.content_loaded(page.url, response)

        facter = JSFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.js',
                value=set([]),
                unit='js',
                title='JS'
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js',
                value=0,
                unit='kb',
                title='Total JS size'
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.js.gzipped',
                value=0,
                unit='kb',
                title='Total JS size gzipped'
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.requests.js',
                value=1,
                title='Total JS requests'
            ))

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
        response = Mock(status_code=200, text=content)
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
