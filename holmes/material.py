#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from functools import partial

from holmes.cli import BaseCLI
from holmes.models.domain import Domain


def configure_materials(girl, db):
    girl.add_material(
        'domains_details',
        partial(Domain.get_domains_details, db),
        30
    )


class MaterialWorker(BaseCLI):
    def initialize(self):
        self.uuid = uuid4().hex

        self.error_handlers = [handler(self.config) for handler in self.load_error_handlers()]

        self.connect_sqlalchemy()
        self.connect_to_redis()

        self.configure_material_girl()

    def do_work(self):
        self.info('Running material girl...')
        self.girl.run()

def main():
    worker = MaterialWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
