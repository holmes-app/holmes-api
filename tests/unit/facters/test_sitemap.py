#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.sitemap import SitemapFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestSitemapFacter(FacterTestCase):

    def test_get_facts(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )
        facter = SitemapFacter(reviewer)
        facter.async_get = Mock()
        facter.get_sitemaps = Mock(return_value=['http://g1.globo.com/sitemap.xml'])
        facter.add_fact = Mock()

        facter.get_facts()

        expect(facter.review.data).to_include('sitemap.data')
        expect(facter.review.data['sitemap.data']).to_equal({})

        expect(facter.review.data).to_include('sitemap.urls')
        expect(facter.review.data['sitemap.urls']).to_equal({})

        expect(facter.review.data).to_include('sitemap.files')
        expect(facter.review.data['sitemap.files']).to_equal(set())

        expect(facter.review.data).to_include('sitemap.files.size')
        expect(facter.review.data['sitemap.files.size']).to_equal({})

        expect(facter.review.data).to_include('sitemap.files.urls')
        expect(facter.review.data['sitemap.files.urls']).to_equal({})

        expect(facter.review.data).to_include('total.size.sitemap')
        expect(facter.review.data['total.size.sitemap']).to_equal(0)

        expect(facter.review.data).to_include('total.size.sitemap.gzipped')
        expect(facter.review.data['total.size.sitemap.gzipped']).to_equal(0)

        expect(facter.add_fact.call_args_list).to_include(
            call(key='total.sitemap.indexes', value=0, unit='', title='Total Sitemap indexes')
        )
        expect(facter.add_fact.call_args_list).to_include(
            call(key='total.sitemap.urls', value=0, unit='', title='Total Sitemap urls')
        )
        expect(facter.add_fact.call_args_list).to_include(
            call(key='total.size.sitemap', value=0, unit='kb', title='Total Sitemap size')
        )
        expect(facter.add_fact.call_args_list).to_include(
            call(key='total.size.sitemap.gzipped', value=0, unit='kb', title='Total Sitemap size gzipped')
        )
        facter.async_get.assert_called_once_with(
            'http://g1.globo.com/robots.txt',
            facter.handle_robots_loaded
        )

    def test_get_sitemaps(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        facter = SitemapFacter(reviewer)
        facter.review.data['robots.response'] = ''

        expect(facter.get_sitemaps(Mock(status_code=404))).to_equal(['http://g1.globo.com/sitemap.xml'])

    def test_get_sitemaps_with_robots_txt(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        facter = SitemapFacter(reviewer)
        response = Mock(status_code=200, text="""
            Sitemap: http://g1.globo.com/1.xml
            Sitemap: http://g1.globo.com/2.xml
            """)

        expect(facter.get_sitemaps(response)).to_equal([
            'http://g1.globo.com/sitemap.xml',
            'http://g1.globo.com/1.xml',
            'http://g1.globo.com/2.xml'
        ])

    def test_handle_sitemap_return_404(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        response = Mock(status_code=404, text='Not found')

        facter = SitemapFacter(reviewer)
        facter.async_get = Mock()
        facter.get_sitemaps = Mock(return_value=['http://g1.globo.com/sitemap.xml'])

        facter.get_facts()
        facter.async_get = Mock()
        facter.handle_sitemap_loaded("http://g1.globo.com/sitemap.xml", response)

        expect(facter.review.data['sitemap.data']["http://g1.globo.com/sitemap.xml"]).to_equal(response)

    def test_handle_sitemap_index_loaded(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        content = self.get_file('index_sitemap.xml')
        response = Mock(status_code=200, text=content)

        facter = SitemapFacter(reviewer)
        facter.async_get = Mock()
        facter.get_sitemaps = Mock(return_value=['http://g1.globo.com/sitemap.xml'])

        facter.get_facts()
        facter.async_get = Mock()
        facter.handle_sitemap_loaded("http://g1.globo.com/sitemap.xml", response)

        expect(facter.review.data['sitemap.files.size']["http://g1.globo.com/sitemap.xml"]).to_equal(0.2607421875)
        expect(facter.review.data['sitemap.urls']["http://g1.globo.com/sitemap.xml"]).to_equal(set())
        expect(facter.review.facts['total.size.sitemap']['value']).to_equal(0.2607421875)
        expect(facter.review.facts['total.size.sitemap.gzipped']['value']).to_equal(0.146484375)
        expect(facter.review.data['total.size.sitemap']).to_equal(0.2607421875)
        expect(facter.review.data['total.size.sitemap.gzipped']).to_equal(0.146484375)
        expect(facter.review.data['sitemap.files.urls']["http://g1.globo.com/sitemap.xml"]).to_equal(2)
        expect(facter.async_get.call_args_list).to_include(
            call('http://domain.com/1.xml', facter.handle_sitemap_loaded),
        )
        expect(facter.async_get.call_args_list).to_include(
            call('http://domain.com/2.xml', facter.handle_sitemap_loaded),
        )

    def test_handle_sitemap_url_loaded(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )
        reviewer.enqueue = Mock()

        content = self.get_file('url_sitemap.xml')
        response = Mock(status_code=200, text=content)

        facter = SitemapFacter(reviewer)
        facter.async_get = Mock()

        facter.get_facts()

        facter.handle_sitemap_loaded("http://g1.globo.com/sitemap.xml", response)

        expect(facter.review.data['sitemap.files.size']["http://g1.globo.com/sitemap.xml"]).to_equal(0.296875)
        expect(facter.review.data['sitemap.urls']["http://g1.globo.com/sitemap.xml"]).to_equal(set(['http://domain.com/1.html', 'http://domain.com/2.html']))
        expect(facter.review.facts['total.size.sitemap']['value']).to_equal(0.296875)
        expect(facter.review.facts['total.size.sitemap.gzipped']['value']).to_equal(0.1494140625)
        expect(facter.review.data['total.size.sitemap']).to_equal(0.296875)
        expect(facter.review.data['total.size.sitemap.gzipped']).to_equal(0.1494140625)
        expect(facter.review.data['sitemap.files.urls']["http://g1.globo.com/sitemap.xml"]).to_equal(2)
        expect(facter.review.facts['total.sitemap.urls']['value']).to_equal(2)
        expect(reviewer.enqueue.call_args_list).to_include(
            call('http://domain.com/1.html'),
        )
        expect(reviewer.enqueue.call_args_list).to_include(
            call('http://domain.com/2.html'),
        )

    def test_handle_robots_loaded(self):
        page = PageFactory.create(url="http://g1.globo.com/")

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )
        facter = SitemapFacter(reviewer)
        facter.async_get = Mock()
        facter.get_sitemaps = Mock(return_value=['http://g1.globo.com/sitemap.xml'])

        facter.handle_robots_loaded('http://g1.globo.com/robots.txt', Mock())

        facter.async_get.assert_called_once_with(
            'http://g1.globo.com/sitemap.xml',
            facter.handle_sitemap_loaded
        )
