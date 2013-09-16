#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase as PythonTestCase

from cow.testing import CowTestCase
from motorengine import connect

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


class ModelTestCase(PythonTestCase):
    @classmethod
    def setUpClass(cls):
        connect(
            "mongo-test",
            host="localhost",
            port=7778
        )
