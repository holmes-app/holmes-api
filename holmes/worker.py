#!/usr/bin/env python
# -*- coding: utf-8 -*-


from holmes.config import Config
from derpconf.config import verify_config

class HolmesWorker(object):
    working = True

    def run(self):
        pass

    def stop_work(self):
        working = False



def main():
    worker = HolmesWorker()
    worker.run()


if __name__ == '__main__':
    main()