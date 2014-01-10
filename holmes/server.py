#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from cow.server import Server
from cow.plugins.sqlalchemy_plugin import SQLAlchemyPlugin
from cow.plugins.redis_plugin import RedisPlugin, CowRedisClient
from tornado.httpclient import AsyncHTTPClient
#from toredis import Client

from holmes.handlers.worker import WorkerHandler, WorkersHandler, WorkersInfoHandler
from holmes.handlers.worker_state import WorkerStateHandler
from holmes.handlers.page import (
    PageHandler, PagesHandler, PageReviewsHandler, PageViolationsPerDayHandler
)
from holmes.handlers.violation import (
    MostCommonViolationsHandler, ViolationsHandler, ViolationHandler
)
from holmes.handlers.review import (
    ReviewHandler, LastReviewsHandler
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
from holmes.event_bus import EventBus, NoOpEventBus
from holmes.utils import load_classes
from holmes.models import Key
from holmes.cache import Cache


def main():
    AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
    HolmesApiServer.run()


class HolmesApiServer(Server):
    def __init__(self, db=None, debug=None, *args, **kw):
        super(HolmesApiServer, self).__init__(*args, **kw)

        self.force_debug = debug
        self.db = db

    def initialize_app(self, *args, **kw):
        super(HolmesApiServer, self).initialize_app(*args, **kw)

        self.application.db = None

        if self.force_debug is not None:
            self.debug = self.force_debug

    def get_handlers(self):
        handlers = [
            (r'/most-common-violations/?', MostCommonViolationsHandler),
            (r'/last-reviews/?', LastReviewsHandler),
            (r'/workers/?', WorkersHandler),
            (r'/workers/info/?', WorkersInfoHandler),
            (r'/worker/([a-z0-9-]*)/(alive|dead)/?', WorkerHandler),
            (r'/worker/([a-z0-9-]*)/(start|complete)/?', WorkerStateHandler),
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
            (r'/violations/?', ViolationsHandler),
            (r'/violation/([a-z0-9\.]*)/?', ViolationHandler),
        ]

        return tuple(handlers)

    def get_plugins(self):
        return [
            SQLAlchemyPlugin,
            RedisPlugin
        ]

    def after_start(self, io_loop):
        if self.db is not None:
            self.application.db = self.db
        else:
            self.application.db = self.application.get_sqlalchemy_session()

        if self.debug:
            import sqltap
            sqltap.start()

        self.application.facters = self._load_facters()
        self.application.validators = self._load_validators()
        self.application.error_handlers = [handler(self.application.config) for handler in self._load_error_handlers()]

        self.application.fact_definitions = {}
        self.application.violation_definitions = {}

        for facter in self.application.facters:
            self.application.fact_definitions.update(facter.get_fact_definitions())

        self._insert_keys(self.application.fact_definitions)

        for validator in self.application.validators:
            self.application.violation_definitions.update(validator.get_violation_definitions())

        self._insert_keys(self.application.violation_definitions)

        self.application.event_bus = NoOpEventBus(self.application)
        self.application.http_client = AsyncHTTPClient(io_loop=io_loop)
        self.connect_pub_sub(io_loop)

        self.application.cache = Cache(self.application)

    def _insert_keys(self, keys):
        for name in keys.keys():
            key = Key.get_or_create(self.application.db, name)
            keys[name]['key'] = key
            self.application.db.add(key)
            self.application.db.flush()
            self.application.db.commit()

    def _load_validators(self):
        return load_classes(default=self.config.VALIDATORS)

    def _load_facters(self):
        return load_classes(default=self.config.FACTERS)

    def _load_error_handlers(self):
        return load_classes(default=self.config.ERROR_HANDLERS)

    def before_end(self, io_loop):
        self.application.db.remove()

        if self.debug:
            import sqltap
            statistics = sqltap.collect()
            sqltap.report(statistics, "report.html")

    def connect_pub_sub(self, io_loop):
        host = self.application.config.get('REDISHOST')
        port = self.application.config.get('REDISPORT')

        logging.info("Connecting pubsub to redis at %s:%d" % (host, port))

        self.application.redis_pub_sub = CowRedisClient(io_loop=io_loop)
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
