#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import datetime
from os.path import abspath, dirname, join

from cow.testing import CowTestCase
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

from holmes.utils import Jwt
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
        # self.server.application.redis.flushdb()

        super(ApiTestCase, self).tearDown()

    def get_config(self):
        return dict(
            SQLALCHEMY_CONNECTION_STRING="mysql+mysqldb://root@localhost:3306/test_holmes",
            SQLALCHEMY_POOL_SIZE=1,
            SQLALCHEMY_POOL_MAX_OVERFLOW=0,
            SQLALCHEMY_AUTO_FLUSH=True,
            COMMIT_ON_REQUEST_END=False,
            REDISPUBSUB=True,
            MATERIAL_GIRL_SENTINEL_HOSTS=['127.0.0.1:57574'],
            MATERIAL_GIRL_REDIS_MASTER='master-test',
            ELASTIC_SEARCH_HOST='localhost',
            ELASTIC_SEARCH_PORT=9200,
            ELASTIC_SEARCH_INDEX='holmes-test',
            REDIS_SENTINEL_HOSTS=['127.0.0.1:57574'],
            REDIS_MASTER='master-test',
        )

    def get_server(self):
        cfg = Config(**self.get_config())
        debug = os.environ.get('DEBUG_TESTS', 'False').lower() == 'true'

        self.server = HolmesApiServer(config=cfg, debug=debug, db=db)

        return self.server

    def get_app(self):
        app = super(ApiTestCase, self).get_app()
        app.http_client = AsyncHTTPClient(self.io_loop)

        # FIXME
        self.server.connect_redis(self.io_loop)
        self.server.connect_redis_pub_sub(self.io_loop)
        self.server._after_start(self.io_loop)

        self.db = app.db
        return app

    def get_auth_cookie(
            self, user_email='simple@user.com', provider='provider',
            token='12345', expiration=datetime(year=5000, month=11, day=30)):

        jwt = Jwt(self.server.application.config.SECRET_KEY)
        token = jwt.encode({
            'sub': user_email, 'iss': provider, 'token': token, 'exp': expiration
        })
        return '='.join(('HOLMES_AUTH_TOKEN', token))

    @gen.coroutine
    def anonymous_fetch(self, url, *args, **kwargs):

        # ensure that the request has no cookies
        if 'headers' in kwargs and 'Cookie' in kwargs['headers']:
            del kwargs['headers']['Cookie']

        response = yield self.http_client.fetch(
            self.get_url(url), *args, **kwargs
        )

        raise gen.Return(response)

    @gen.coroutine
    def authenticated_fetch(self, url, user_email=None, *args, **kwargs):

        # ensure that the request has a valid auth token cookie
        cookie_header = {'Cookie': self.get_auth_cookie(user_email)}
        if 'headers' in kwargs:
            if kwargs['headers'] and 'Cookie' in kwargs['headers']:
                cookie_header = {
                    'Cookie': '; '.join(
                        (kwargs['headers']['Cookie'], cookie_header['Cookie'])
                    )
                }
            kwargs['headers'].update(cookie_header)
        else:
            kwargs['headers'] = cookie_header

        response = yield self.http_client.fetch(
            self.get_url(url), *args, **kwargs
        )

        raise gen.Return(response)

    def connect_to_sync_redis(self):
        from holmes.utils import get_redis
        from holmes.cache import SyncCache

        redis = get_redis(
            self.server.application.config.get('REDIS_SENTINEL_HOSTS'),
            self.server.application.config.get('REDIS_MASTER'),
            self.server.application.config.get('REDISPASS')
        )
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
