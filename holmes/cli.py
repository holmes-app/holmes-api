#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from sheep import Shepherd
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from materialgirl import Materializer
from materialgirl.storage.redis import RedisStorage

from holmes.cache import SyncCache
from holmes.utils import load_classes, get_redis_port_host, get_redis
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

    def load_authnz_wrapper(self):
        authnz_wrapper_class_name = self.config.get('AUTHNZ_WRAPPER', None)
        if authnz_wrapper_class_name:
            authnz_wrapper_list = load_classes(default=[authnz_wrapper_class_name])
            if isinstance(authnz_wrapper_list, list) and len(authnz_wrapper_list) == 1:
                return authnz_wrapper_list.pop()
        return None

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
        host, port = get_redis_port_host(
            self.config.get('REDIS_SENTINEL_HOSTS'),
            self.config.get('REDIS_MASTER')
        )

        self.info("Connecting to redis at %s:%d" % (host, port))
        self.redis = get_redis(
            self.config.get('REDIS_SENTINEL_HOSTS'),
            self.config.get('REDIS_MASTER'),
            self.config.get('REDISPASS')
        )

        self.cache = SyncCache(self.db, self.redis, self.config)

        self.info("Connecting pubsub to redis at %s:%d" % (host, port))
        self.redis_pub_sub = get_redis(
            self.config.get('REDIS_SENTINEL_HOSTS'),
            self.config.get('REDIS_MASTER'),
            self.config.get('REDISPASS')
        )

        host, port = get_redis_port_host(
            self.config.get('MATERIAL_GIRL_SENTINEL_HOSTS'),
            self.config.get('MATERIAL_GIRL_REDIS_MASTER')
        )

        self.info("Connecting material girl to redis at %s:%d" % (host, port))
        self.redis_material = get_redis(
            self.config.get('MATERIAL_GIRL_SENTINEL_HOSTS'),
            self.config.get('MATERIAL_GIRL_REDIS_MASTER'),
            self.config.get('MATERIAL_GIRL_REDISPASS')
        )

    def configure_material_girl(self):
        from holmes.material import configure_materials
        self.girl = Materializer(storage=RedisStorage(redis=self.redis_material))

        configure_materials(self.girl, self.db, self.config)
