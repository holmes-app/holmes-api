#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import UUID
from ujson import loads

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Page, Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestPageHandler(ApiTestCase):

    @gen_test
    def test_can_save(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body='url=%s' % 'http://globo.com'
        )

        expect(response.code).to_equal(200)

        page_uuid = UUID(response.body)
        page = yield Page.objects.get(uuid=page_uuid)

        expect(page).not_to_be_null()
        expect(page_uuid).to_equal(page.uuid)

    @gen_test
    def test_can_save_known_domain(self):
        yield Domain.objects.create(url='http://globo.com', name='globo.com')

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body='url=%s' % 'http://globo.com'
        )

        expect(response.code).to_equal(200)

        page_uuid = UUID(response.body)
        page = yield Page.objects.get(uuid=page_uuid)

        expect(page).not_to_be_null()
        expect(page_uuid).to_equal(page.uuid)

    @gen_test
    def test_error_when_invalid_url(self):
        invalid_url = ''

        try:
            yield self.http_client.fetch(
                self.get_url('/page'),
                method='POST',
                body='url=%s' % invalid_url
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like('Invalid url [%s]' % invalid_url)

        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_when_url_already_exists(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body='url=%s' % page.url
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal(str(page.uuid))

    @gen_test
    def test_get_page_not_found(self):
        invalid_page_uuid = '00000000-0000-0000-0000-000000000000'

        try:
            yield self.http_client.fetch(
                self.get_url('/page/%s' % invalid_page_uuid),
                method='GET'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Page UUID [%s] not found' % invalid_page_uuid)
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_get_page_get_info(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        response = yield self.http_client.fetch(self.get_url('/page/%s' % page.uuid))

        expect(response.code).to_equal(200)

        returned_page = loads(response.body)

        expect(returned_page['uuid']).to_equal(str(page.uuid))
        expect(returned_page['url']).to_equal(page.url)


class TestPagesHandler(ApiTestCase):

    @gen_test
    def test_can_save_with_no_urls(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body=''
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(0)

    @gen_test
    def test_can_save(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        urls = ['http://%d.globo.com/%d.html' % (num, num) for num in range(1000)]

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(1000)

    @gen_test
    def test_saves_only_new_pages(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        domain = yield DomainFactory.create(name='globo.com', url='http://globo.com')
        page = yield PageFactory.create(domain=domain, url='http://www.globo.com/')

        urls = ['http://%d.globo.com/%d.html' % (num, num) for num in range(10)]
        urls.append(page.url)

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(10)

    @gen_test
    def test_saves_does_nothing_if_all_pages_already_there(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        domain = yield DomainFactory.create(name='globo.com', url='http://globo.com')
        page = yield PageFactory.create(domain=domain, url='http://www.globo.com/')

        urls = [page.url]

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(0)

    @gen_test
    def test_cant_save_invalid_urls(self):
        yield Domain.objects.delete()
        yield Page.objects.delete()

        urls = ['/%d.html' % num for num in range(1000)]

        try:
            yield self.http_client.fetch(
                self.get_url('/pages'),
                method='POST',
                body="&".join(['url=%s' % url for url in urls])
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_equal('In the urls you posted there is an invalid URL: /0.html')
        else:
            assert False, 'Should not have gotten this far'

    @gen_test
    def test_pages_will_return_options(self):

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='OPTIONS'
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal('OK')
        expect('Access-Control-Allow-Origin' in response.headers).to_be_true()
        expect(response.headers['Access-Control-Allow-Origin']).to_be_like('*')
