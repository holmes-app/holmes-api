#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

from cow.testing import CowTestCase
from factory import base
from tornado.concurrent import return_future

from holmes.config import Config
from holmes.server import HolmesApiServer


class ApiTestCase(CowTestCase):
    def get_config(self):
        return dict(
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


class MotorEngineFactory(base.Factory):
    """Factory for motorengine objects."""
    ABSTRACT_FACTORY = True

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        return target_class(*args, **kwargs)

    @classmethod
    @return_future
    def _create(cls, target_class, *args, **kwargs):
        callback = kwargs.get('callback', None)
        del kwargs['callback']
        instance = target_class(*args, **kwargs)
        instance.save(callback=callback)


PAGES_ROOT_PATH = abspath(join(dirname(__file__), 'pages'))


class ValidatorTestCase(ApiTestCase):

    def get_page(self, name):
        with open(join(PAGES_ROOT_PATH.rstrip('/'), name.lstrip('/')), 'r') as page:
            return page.read()
