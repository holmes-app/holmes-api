#!/usr/bin/python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

from preggy import expect
from mock import patch, Mock, call
from octopus import TornadoOctopus
from materialgirl import Materializer

from colorama import Fore, Style
from holmes.worker import HolmesWorker
from holmes.config import Config
from tests.unit.base import ApiTestCase
from tests.fixtures import (
    DomainsViolationsPrefsFactory, DomainFactory, KeyFactory
)

class MockResponse(object):
    def __init__(self, status_code=200, text=''):
        self.status_code = status_code
        self.text = text


class WorkerTestCase(ApiTestCase):
    root_path = abspath(join(dirname(__file__), '..', '..'))

    @patch('uuid.UUID')
    def test_initialize(self, uuid):
        uuid.return_value = Mock(hex='my-uuid4')

        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])
        worker.initialize()

        expect(worker.uuid).to_equal('my-uuid4')

        expect(worker.facters).to_length(1)
        expect(worker.validators).to_length(1)

        expect(worker.otto).to_be_instance_of(TornadoOctopus)

        expect(worker.girl).to_be_instance_of(Materializer)

    def test_config_parser(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        parser_mock = Mock()

        worker.config_parser(parser_mock)

        expect(parser_mock.add_argument.call_args_list).to_include(
            call(
                '--concurrency',
                '-t',
                type=int,
                default=10,
                help='Number of threads (or async http requests) to use for '
                     'Octopus (doing GETs concurrently)'
            ))

        expect(parser_mock.add_argument.call_args_list).to_include(
            call(
                '--cache',
                default=False,
                action='store_true',
                help='Whether http requests should be cached by Octopus.'
            ))

    def test_description(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expected = "%s%sholmes-worker-%s%s" % (
            Fore.BLUE,
            Style.BRIGHT,
            '',
            Style.RESET_ALL,
        )

        expect(worker.get_description()).to_be_like(expected)

    def test_config_class(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf')])

        expect(worker.get_config_class()).to_equal(Config)

    def test_load_all_domains_violations_prefs(self):
        worker = HolmesWorker(['-c', join(self.root_path, 'tests/unit/test_worker.conf'), '--concurrency=10'])

        worker.initialize()

        # Same instance of DB, for sqlalchemy runs on Vegas
        bkp_db = worker.db
        worker.db = self.db
        worker.cache.db = self.db

        domain = DomainFactory.create(name='globo.com')

        worker.cache.redis.delete('violations-prefs-%s' % domain.name)

        prefs = worker.cache.redis.get('violations-prefs-%s' % domain.name)
        expect(prefs).to_be_null()

        for i in range(3):
            DomainsViolationsPrefsFactory.create(
                domain=domain,
                key=KeyFactory.create(name='some.random.%d' % i),
                value='v%d' % i
            )

        worker.load_all_domains_violations_prefs()

        prefs = worker.cache.get_domain_violations_prefs('globo.com')

        expect(prefs).to_equal([
            {'value': u'v0', 'key': u'some.random.0'},
            {'value': u'v1', 'key': u'some.random.1'},
            {'value': u'v2', 'key': u'some.random.2'}
        ])

        # Back to the wonderland
        worker.db = bkp_db
        worker.cache.db = bkp_db
