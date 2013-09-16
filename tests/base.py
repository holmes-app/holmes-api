#!/usr/bin/env python
# -*- coding: utf-8 -*-


from cow.testing import CowTestCase

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
