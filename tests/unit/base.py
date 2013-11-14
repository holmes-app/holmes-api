#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

from cow.testing import CowTestCase
from tornado.httpclient import AsyncHTTPClient

from holmes.config import Config
from holmes.server import HolmesApiServer
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory, FactFactory, ViolationFactory, WorkerFactory


class ApiTestCase(CowTestCase):
    ZERO_UUID = '00000000-0000-0000-0000-000000000000'

    def drop_collection(self, document):
        document.objects.delete(callback=self.stop)
        self.wait()

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.db = self.server.application.sqlalchemy_db
        DomainFactory.FACTORY_SESSION = self.db
        PageFactory.FACTORY_SESSION = self.db
        ReviewFactory.FACTORY_SESSION = self.db
        FactFactory.FACTORY_SESSION = self.db
        ViolationFactory.FACTORY_SESSION = self.db
        WorkerFactory.FACTORY_SESSION = self.db
        #self.drop_collection(Domain)
        #self.drop_collection(Page)
        #self.drop_collection(Review)
        #self.drop_collection(Worker)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()
        self.db.rollback()

    def get_config(self):
        return dict(
            SQLALCHEMY_CONNECTION_STRING="mysql+mysqldb://root@localhost:3306/test_holmes",
            SQLALCHEMY_POOL_SIZE=20,
            SQLALCHEMY_POOL_MAX_OVERFLOW=10,
            SQLALCHEMY_AUTO_FLUSH=True,
            COMMIT_ON_REQUEST_END=False,
            MONGO_DATABASES={
                'default': {
                    'host': 'localhost',
                    'port': 6686,
                    'database': 'holmes-test'
                }
            }
        )

    def get_server(self):
        cfg = Config(**self.get_config())
        self.server = HolmesApiServer(config=cfg)
        return self.server

    def get_app(self):
        app = super(ApiTestCase, self).get_app()
        app.http_client = AsyncHTTPClient(self.io_loop)
        return app

FILES_ROOT_PATH = abspath(join(dirname(__file__), 'files'))


class ValidatorTestCase(ApiTestCase):

    def get_file(self, name):
        with open(join(FILES_ROOT_PATH.rstrip('/'), name.lstrip('/')), 'r') as local_file:
            return local_file.read()
