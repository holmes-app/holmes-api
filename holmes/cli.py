#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sheep import Shepherd
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import redis
from materialgirl import Materializer
from materialgirl.storage.redis import RedisStorage

from holmes.cache import SyncCache
from holmes.utils import load_classes
from holmes.config import Config


class BaseCLI(Shepherd):
    def info(self, message):
        self.log(message, logging.info)

    def debug(self, message):
        self.log(message, logging.debug)

    def warn(self, message):
        self.log(message, logging.warn)

    def error(self, message):
        self.log(message, logging.error)

    def log(self, message, level=logging.info):
        name = self.get_description()
        level('[%s - %s] %s' % (
            name, self.parent_name, message
        ))

    def load_error_handlers(self):
        return load_classes(default=self.config.ERROR_HANDLERS)

    def load_search_provider(self):
        search_provider = load_classes(default=[self.config.SEARCH_PROVIDER])
        if isinstance(search_provider, list) and len(search_provider) == 1:
            return search_provider.pop()
        else:
            raise Exception('A search provider must be defined!')

    def get_config_class(self):
        return Config

    def connect_sqlalchemy(self):
        if getattr(self, 'db', None) is not None:
            self.db.close()

        autoflush = self.config.get('SQLALCHEMY_AUTO_FLUSH')
        connstr = self.config.SQLALCHEMY_CONNECTION_STRING
        engine = create_engine(
            connstr,
            convert_unicode=True,
            pool_size=self.config.SQLALCHEMY_POOL_SIZE,
            max_overflow=self.config.SQLALCHEMY_POOL_MAX_OVERFLOW,
            echo=self.options.verbose == 3
        )

        self.info("Connecting to \"%s\" using SQLAlchemy" % connstr)

        self.sqlalchemy_db_maker = sessionmaker(bind=engine, autoflush=autoflush)
        self.db = scoped_session(self.sqlalchemy_db_maker)

    def connect_to_redis(self):
        host = self.config.get('REDISHOST')
        port = self.config.get('REDISPORT')

        self.info("Connecting to redis at %s:%d" % (host, port))
        self.redis = redis.StrictRedis(host=host, port=port, db=0)

        self.cache = SyncCache(self.db, self.redis, self.config)

        self.info("Connecting pubsub to redis at %s:%d" % (host, port))
        self.redis_pub_sub = redis.StrictRedis(host=host, port=port, db=0)

        host = self.config.get('MATERIAL_GIRL_REDISHOST')
        port = self.config.get('MATERIAL_GIRL_REDISPORT')

        self.info("Connecting material girl to redis at %s:%d" % (host, port))
        self.redis_material = redis.StrictRedis(host=host, port=port, db=0)

    def configure_material_girl(self):
        from holmes.material import configure_materials
        self.girl = Materializer(storage=RedisStorage(redis=self.redis_material))

        configure_materials(self.girl, self.db, self.config)
