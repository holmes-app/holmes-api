#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from os.path import abspath, dirname, join

from cow.testing import CowTestCase
from tornado.httpclient import AsyncHTTPClient

from holmes.config import Config
from holmes.server import HolmesApiServer
from tests.fixtures import db


class ApiTestCase(CowTestCase):
    ZERO_UUID = '00000000-0000-0000-0000-000000000000'

    def drop_collection(self, document):
        document.objects.delete(callback=self.stop)
        self.wait()

    def tearDown(self):
        self.db.rollback()
        self.server.application.redis.flushdb()
        super(ApiTestCase, self).tearDown()

    def get_config(self):
        return dict(
            SQLALCHEMY_CONNECTION_STRING="mysql+mysqldb://root@localhost:3306/test_holmes",
            SQLALCHEMY_POOL_SIZE=1,
            SQLALCHEMY_POOL_MAX_OVERFLOW=0,
            SQLALCHEMY_AUTO_FLUSH=True,
            COMMIT_ON_REQUEST_END=False,
            REDISHOST='localhost',
            REDISPORT=57575,
            MATERIAL_GIRL_REDISHOST='localhost',
            MATERIAL_GIRL_REDISPORT=57575,
            ELASTIC_SEARCH_HOST='localhost',
            ELASTIC_SEARCH_PORT=9200,
            ELASTIC_SEARCH_INDEX='holmes-test',
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

    def connect_to_sync_redis(self):
        import redis
        from holmes.cache import SyncCache

        host = self.server.application.config.get('REDISHOST')
        port = self.server.application.config.get('REDISPORT')

        redis = redis.StrictRedis(host=host, port=port, db=0)

        return SyncCache(self.db, redis, self.server.application.config)

    def use_no_external_search_provider(self):
        from holmes.search_providers.noexternal import NoExternalSearchProvider
        self.server.application.search_provider = NoExternalSearchProvider(
            config=self.server.application.config,
            db=self.db,
            io_loop=self.io_loop
        )

    def use_elastic_search_provider(self):
        from holmes.search_providers.elastic import ElasticSearchProvider
        self.server.application.search_provider = ElasticSearchProvider(
            config=self.server.application.config,
            db=self.db,
            io_loop=self.io_loop
        )

FILES_ROOT_PATH = abspath(join(dirname(__file__), 'files'))


class ValidatorTestCase(ApiTestCase):

    def get_file(self, name):
        with open(join(FILES_ROOT_PATH.rstrip('/'), name.lstrip('/')), 'r') as local_file:
            return local_file.read()

    @property
    def sync_cache(self):
        return self.connect_to_sync_redis()

class FacterTestCase(ValidatorTestCase):
    pass
