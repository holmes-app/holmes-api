#!/usr/bin/python
# -*- coding: utf-8 -*-

from cow.server import Server
from cow.plugins.motorengine_plugin import MotorEnginePlugin

from holmes.handlers.worker import WorkerPingHandler
from holmes.handlers.page import PageHandler
from holmes.handlers.fact import CreateFactHandler
from holmes.handlers.violation import CreateViolationHandler
from holmes.handlers.review import ReviewHandler


def main():
    HolmesApiServer.run()


class HolmesApiServer(Server):
    def get_handlers(self):
        handlers = [
            (r'/worker/ping', WorkerPingHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/fact/?', CreateFactHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/violation/?', CreateViolationHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/?', ReviewHandler),
            (r'/page/([a-z0-9-]*)/?', PageHandler),
            (r'/page/?', PageHandler),
        ]

        return tuple(handlers)

    def get_plugins(self):
        return [
            MotorEnginePlugin,
        ]


if __name__ == '__main__':
    main()
