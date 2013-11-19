#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from cow.server import Server
#from cow.plugins.motorengine_plugin import MotorEnginePlugin
from cow.plugins.sqlalchemy_plugin import SQLAlchemyPlugin
from cow.plugins.redis_plugin import RedisPlugin
from tornado.httpclient import AsyncHTTPClient
from toredis import Client

from holmes.handlers.worker import WorkerHandler, WorkersHandler
from holmes.handlers.worker_state import WorkerStateHandler
from holmes.handlers.page import (
    PageHandler, PagesHandler, PageReviewsHandler, PageViolationsPerDayHandler
)
from holmes.handlers.fact import CreateFactHandler
from holmes.handlers.violation import (
    CreateViolationHandler, MostCommonViolationsHandler
)
from holmes.handlers.review import (
    ReviewHandler, CompleteReviewHandler, LastReviewsHandler
)
from holmes.handlers.next_job import NextJobHandler
from holmes.handlers.domains import (
    DomainsHandler, DomainDetailsHandler, DomainViolationsPerDayHandler,
    DomainReviewsHandler
)
from holmes.handlers.search import (
    SearchHandler
)
from holmes.handlers.bus import EventBusHandler
from holmes.event_bus import EventBus


def main():
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    HolmesApiServer.run()


class HolmesApiServer(Server):
    def get_handlers(self):
        handlers = [
            (r'/most-common-violations/?', MostCommonViolationsHandler),
            (r'/last-reviews/?', LastReviewsHandler),
            (r'/workers/?', WorkersHandler),
            (r'/worker/([a-z0-9-]*)/(alive|dead)/?', WorkerHandler),
            (r'/worker/([a-z0-9-]*)/(start|complete)/?', WorkerStateHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/complete/?', CompleteReviewHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/fact/?', CreateFactHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/violation/?', CreateViolationHandler),
            (r'/page/([a-z0-9-]*)/review/([a-z0-9-]*)/?', ReviewHandler),
            (r'/page/([a-z0-9-]*)/reviews/?', PageReviewsHandler),
            (r'/page/([a-z0-9-]*)/violations-per-day/?', PageViolationsPerDayHandler),
            (r'/page/([a-z0-9-]*)/?', PageHandler),
            (r'/search/?', SearchHandler),
            (r'/page/?', PageHandler),
            (r'/pages/?', PagesHandler),
            (r'/domains/?', DomainsHandler),
            (r'/domains/([^/]+)/?', DomainDetailsHandler),
            (r'/domains/([^/]+)/violations-per-day/?', DomainViolationsPerDayHandler),
            (r'/domains/([^/]+)/reviews/?', DomainReviewsHandler),
            (r'/next/?', NextJobHandler),
            (r'/events/?', EventBusHandler),
        ]

        return tuple(handlers)

    def get_plugins(self):
        return [
            SQLAlchemyPlugin,
            RedisPlugin
        ]

    def after_start(self, io_loop):
        self.application.http_client = AsyncHTTPClient(io_loop=io_loop)
        self.connect_pub_sub(io_loop)

    def connect_pub_sub(self, io_loop):
        host = self.application.config.get('REDISHOST')
        port = self.application.config.get('REDISPORT')

        logging.info("Connecting pubsub to redis at %s:%d" % (host, port))

        self.application.redis_pub_sub = Client(io_loop=io_loop)
        self.application.redis_pub_sub.authenticated = False
        self.application.redis_pub_sub.connect(host, port, callback=self.has_connected(self.application))

    def has_connected(self, application):
        def handle(*args, **kw):
            password = application.config.get('REDISPASS', None)
            if password:
                application.redis_pub_sub.auth(password, callback=self.handle_authenticated(application))
            else:
                self.handle_authenticated(application)()
        return handle

    def handle_authenticated(self, application):
        def handle(*args, **kw):
            application.redis_pub_sub.authenticated = True
            application.event_bus = EventBus(self.application)  # can now connect to redis using pubsub

        return handle

if __name__ == '__main__':
    main()
