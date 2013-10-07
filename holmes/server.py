#!/usr/bin/python
# -*- coding: utf-8 -*-

from cow.server import Server
from cow.plugins.motorengine_plugin import MotorEnginePlugin

from holmes.handlers.worker import WorkerHandler, WorkersHandler
from holmes.handlers.worker_state import WorkerStateHandler
from holmes.handlers.page import PageHandler
from holmes.handlers.fact import CreateFactHandler
from holmes.handlers.violation import CreateViolationHandler
from holmes.handlers.review import ReviewHandler, CompleteReviewHandler
from holmes.handlers.next_job import NextJobHandler


def main():
    HolmesApiServer.run()


class HolmesApiServer(Server):
    def get_handlers(self):
        handlers = [
            (r'/workers/?', WorkersHandler),
            (r'/worker/([a-z0-9-]*)/ping', WorkerHandler),
            (r'/worker/([a-z0-9-]*)/(start|complete)/([a-z0-9-]*)', WorkerStateHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/complete/?', CompleteReviewHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/fact/?', CreateFactHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/violation/?', CreateViolationHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/?', ReviewHandler),
            (r'/page/([a-z0-9-]*)/?', PageHandler),
            (r'/page/?', PageHandler),
            (r'/next/?', NextJobHandler),
        ]

        return tuple(handlers)

    def get_plugins(self):
        return [
            MotorEnginePlugin,
        ]


if __name__ == '__main__':
    main()
