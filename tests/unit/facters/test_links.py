#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.links import LinkFacter
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestMetaTagsFacter(ValidatorTestCase):

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
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = LinkFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.review.data).to_include('page.links')
        expect(facter.review.data['page.links']).to_equal(set([]))

        expect(facter.review.data).to_include('page.all_links')
        link = facter.review.data['page.all_links'][1]
        expect(link.tag).to_equal('a')
        expect(link.get('href')).to_equal('/')
        expect(link.get('title')).to_equal('globo.com')

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.links',
                value=set([]),
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.number.links',
                value=4,
            ))

        expect(facter.async_get.call_args_list).to_include(
            call(
                'http://my-site.com/privacidade.html',
                facter.handle_url_loaded
            ))

        expect(facter.async_get.call_args_list).to_include(
            call(
                'http://my-site.com/',
                facter.handle_url_loaded
            ))

        expect(facter.async_get.call_args_list).to_include(
            call(
                'http://my-site.com/todos-os-sites.html',
                facter.handle_url_loaded
            ))

    def test_handle_url_loaded(self):
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

        facter = LinkFacter(reviewer)
        facter.async_get = Mock()
        facter.get_facts()

        facter.handle_url_loaded(page.url, response)

        expect(facter.review.data).to_include('page.links')
        data = set([(page.url, response)])
        expect(facter.review.data['page.links']).to_equal(data)

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = LinkFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect('page.links' in definitions).to_be_true()
        expect('total.number.links' in definitions).to_be_true()

    def test_link_looks_like_image(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<a href="http://globo.com/metal.png">Metal</a>'

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

        facter = LinkFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.links',
                value=set([])
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.number.links',
                value=0
            ))

        expect(facter.async_get.called).to_be_false()
