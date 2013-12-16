#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.images import ImageFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestImageFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = '<img src="test.png" alt="a" title="b" /><img src="" />'

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

        facter = ImageFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(3)

        expect(facter.review.data).to_include('page.all_images')

        img = facter.review.data['page.all_images'][0]
        expect(img.tag).to_equal('img')
        expect(img.get('src')).to_equal('test.png')

        expect(facter.review.data).to_include('page.images')
        expect(facter.review.data['page.images']).to_equal(set([]))

        expect(facter.review.data).to_include('total.size.img')
        expect(facter.review.data['total.size.img']).to_equal(0)

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.images',
                value=set([]),
            ))

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.size.img',
                value=0,
            )),

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='total.requests.img',
                value=1,
            ))

        facter.async_get.assert_called_once_with(
            'http://my-site.com/test.png',
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

        content = '<img src="test.png" alt="a" title="b" />'

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

        facter = ImageFacter(reviewer)
        facter.async_get = Mock()
        facter.get_facts()

        facter.handle_url_loaded(page.url, response)

        expect(facter.review.data).to_include('page.all_images')
        expect(facter.review.data['page.all_images']).to_equal([])

        expect(facter.review.data).to_include('page.images')
        data = set([(page.url, response)])
        expect(facter.review.data['page.images']).to_equal(data)

        expect(facter.review.data).to_include('total.size.img')
        expect(facter.review.data['total.size.img']).to_equal(0.0390625)

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = ImageFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(3)
        expect('page.images' in definitions).to_be_true()
        expect('total.size.img' in definitions).to_be_true()
        expect('total.requests.img' in definitions).to_be_true()
