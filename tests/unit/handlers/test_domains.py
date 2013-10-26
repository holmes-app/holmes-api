#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory


class TestDomainsHandler(ApiTestCase):

    @gen_test
    def test_can_save(self):
        yield Domain.objects.delete()
        yield DomainFactory.create(url="http://globo.com", name="globo.com")
        yield DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(2)

        expect(domains[0]['name']).to_equal("g1.globo.com")
        expect(domains[0]['url']).to_equal("http://g1.globo.com")
        expect(domains[0]['violationCount']).to_equal(0)
        expect(domains[0]['pageCount']).to_equal(0)

        expect(domains[1]['name']).to_equal("globo.com")
        expect(domains[1]['url']).to_equal("http://globo.com")
        expect(domains[1]['violationCount']).to_equal(0)
        expect(domains[1]['pageCount']).to_equal(0)

    @gen_test
    def test_will_return_empty_list_when_no_domains(self):
        yield Domain.objects.delete()

        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(0)
