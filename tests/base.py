#!/usr/bin/env python
# -*- coding: utf-8 -*-


from cow.testing import CowTestCase
from factory import base
from tornado.concurrent import return_future

from holmes.config import Config
from holmes.server import HolmesApiServer


class ApiTestCase(CowTestCase):
    def get_server(self):
        cfg = Config(
            MONGO_DATABASES={
                'default': {
                    'host': 'localhost',
                    'port': 6686,
                    'database': 'holmes-test'
                }
            }
        )

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
