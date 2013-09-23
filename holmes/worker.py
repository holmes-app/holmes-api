#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
from os.path import abspath, dirname, join
from holmes.config import Config
from holmes.reviewer import Reviewer
from derpconf.config import verify_config
from optparse import OptionParser


class HolmesWorker(object):

    def __init__(self, arguments=[]):
        self.root_path = abspath(join(dirname(__file__), ".."))

        self.working = True
        self.config = None
        self.validators = set()
        
        self._parse_opt(arguments)
        self._load_config(self.options.verbose == 3)

    def run(self):
        try:
            while self.working:
                self._do_work()
                time.sleep(self.config.WORKER_SLEEP_TIME)
        except KeyboardInterrupt:
            self.working = False

    def stop_work(self):
        self.working = False

    def _do_work(self):
        pages = self._load_new_pages()

        for page in pages:
            Reviewer(page, self.config, self.validators)

    def _load_new_pages(self):
        return ["http://www.globo.com", "http://g1.globo.com"]

    def _parse_opt(self, arguments):
        parser = OptionParser()
        parser.add_option('-c', '--conf', dest='conf', default=join(self.root_path, 'holmes/config/local.conf'),
                          help='Configuration file to use for the server.')
        parser.add_option('--verbose', '-v', action='count',
                          help='Log level: v=warning, vv=info, vvv=debug.')
        
        self.options, self.arguments = parser.parse_args(arguments)

    def _load_config(self, verify=False):
        if verify:
            verify_config(self.options.conf)
        self.config = Config.load(self.options.conf)


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
