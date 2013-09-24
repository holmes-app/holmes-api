#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import logging
from os.path import abspath, dirname, join
from derpconf.config import verify_config
from optparse import OptionParser
from holmes.config import Config
from holmes.reviewer import Reviewer


class HolmesWorker(object):

    def __init__(self, arguments=[]):
        self.root_path = abspath(join(dirname(__file__), ".."))

        self.working = True
        self.config = None
        self.validators = set()
        
        self._parse_opt(arguments)
        self._load_config(self.options.verbose == 3)
        self._config_logging()

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
        page = self._load_next_page_from_api()
        Reviewer(page, self.config, self.validators)

    def _load_next_page_from_api(self):
        return {"url": "http://globo.com", "page_id": 1}

    def _parse_opt(self, arguments):
        parser = OptionParser()
        parser.add_option('-c', '--conf', dest='conf', default=join(self.root_path, 'holmes/config/local.conf'),
                          help='Configuration file to use for the server.')
        parser.add_option('--verbose', '-v', action='count', default=0,
                          help='Log level: v=warning, vv=info, vvv=debug.')
        
        self.options, self.arguments = parser.parse_args(arguments)

    def _load_config(self, verify=False):
        if verify:
            verify_config(self.options.conf)
        self.config = Config.load(self.options.conf)

    def _config_logging(self):
        LOGS = {
            0: 'error',
            1: 'warning',
            2: 'info',
            3: 'debug'
        }

        if self.options.verbose:
            log_level = LOGS[self.options.verbose].upper()
        else:
            log_level = self.config.LOG_LEVEL.upper()

        logging.basicConfig(
            level=log_level,
            format=self.config.LOG_FORMAT,
            datefmt=self.config.LOG_DATE_FORMAT
        )

        return log_level


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
