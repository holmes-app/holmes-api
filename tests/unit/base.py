#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import abspath, dirname, join

from cow.testing import CowTestCase

from holmes.config import Config
from holmes.server import HolmesApiServer
from holmes.models import Domain, Page, Review, Worker


class ApiTestCase(CowTestCase):
    ZERO_UUID = '00000000-0000-0000-0000-000000000000'

    def drop_collection(self, document):
        document.objects.delete(callback=self.stop)
        self.wait()

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.drop_collection(Domain)
        self.drop_collection(Page)
        self.drop_collection(Review)
        self.drop_collection(Worker)

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


FILES_ROOT_PATH = abspath(join(dirname(__file__), 'files'))


class ValidatorTestCase(ApiTestCase):

    def get_file(self, name):
        with open(join(FILES_ROOT_PATH.rstrip('/'), name.lstrip('/')), 'r') as local_file:
            return local_file.read()
