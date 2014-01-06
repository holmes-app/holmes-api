#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import abspath, dirname, join

from cow.testing import CowTestCase
from tornado.httpclient import AsyncHTTPClient
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from holmes.config import Config
from holmes.server import HolmesApiServer
from tests.fixtures import (
    DomainFactory, PageFactory, ReviewFactory, FactFactory,
    ViolationFactory, WorkerFactory, KeyFactory
)


autoflush = True
engine = create_engine(
    "mysql+mysqldb://root@localhost:3306/test_holmes",
    convert_unicode=True,
    pool_size=1,
    max_overflow=0,
    echo=False
)
maker = sessionmaker(bind=engine, autoflush=autoflush)
db = scoped_session(maker)


class ApiTestCase(CowTestCase):
    ZERO_UUID = '00000000-0000-0000-0000-000000000000'

    def drop_collection(self, document):
        document.objects.delete(callback=self.stop)
        self.wait()

    def setUp(self):
        super(ApiTestCase, self).setUp()

        DomainFactory.FACTORY_SESSION = self.db
        PageFactory.FACTORY_SESSION = self.db
        ReviewFactory.FACTORY_SESSION = self.db
        FactFactory.FACTORY_SESSION = self.db
        ViolationFactory.FACTORY_SESSION = self.db
        WorkerFactory.FACTORY_SESSION = self.db
        KeyFactory.FACTORY_SESSION = self.db

        self.clean_cache('globo.com')
        self.clean_cache('g1.globo.com')

    def tearDown(self):
        self.db.rollback()
        super(ApiTestCase, self).tearDown()

    def get_config(self):
        return dict(
            SQLALCHEMY_CONNECTION_STRING="mysql+mysqldb://root@localhost:3306/test_holmes",
            SQLALCHEMY_POOL_SIZE=1,
            SQLALCHEMY_POOL_MAX_OVERFLOW=0,
            SQLALCHEMY_AUTO_FLUSH=True,
            COMMIT_ON_REQUEST_END=False,
        )

    def get_server(self):
        cfg = Config(**self.get_config())
        debug = os.environ.get('DEBUG_TESTS', 'False').lower() == 'true'

        self.server = HolmesApiServer(config=cfg, debug=debug, db=db)
        return self.server

    def get_app(self):
        app = super(ApiTestCase, self).get_app()
        app.http_client = AsyncHTTPClient(self.io_loop)
        self.db = app.db

        return app

    def clean_cache(self, domain_name):
        self.server.application.redis.delete('%s-page-count' % domain_name)
        self.server.application.redis.delete('%s-violation-count' % domain_name)
        self.server.application.redis.delete('%s-active-review-count' % domain_name)

FILES_ROOT_PATH = abspath(join(dirname(__file__), 'files'))


class ValidatorTestCase(ApiTestCase):

    def get_file(self, name):
        with open(join(FILES_ROOT_PATH.rstrip('/'), name.lstrip('/')), 'r') as local_file:
            return local_file.read()


class FacterTestCase(ValidatorTestCase):
    pass
