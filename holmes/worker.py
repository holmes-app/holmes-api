#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from holmes.config import Config
from derpconf.config import verify_config

class HolmesWorker(object):
    working = True

    def run(self):
        try:
            while self.working:
                self.do_work()
        except KeyboardInterrupt:
            return True

    def stop_work(self):
        self.working = False

    def do_work(self):
        print "."


def main():
    worker = HolmesWorker()
    worker.run()


if __name__ == '__main__':
    main()