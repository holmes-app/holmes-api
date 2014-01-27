#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from uuid import uuid4
from datetime import datetime, timedelta

from ujson import dumps
from sheep import Shepherd
from colorama import Fore, Style
from octopus import TornadoOctopus
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import OperationalError
import redis

from holmes import __version__
from holmes.cache import SyncCache
from holmes.config import Config
from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.utils import load_classes
from holmes.models import Settings, Worker, Page


class BaseWorker(Shepherd):
    def info(self, message):
        self.log(message, logging.info)

    def debug(self, message):
        self.log(message, logging.debug)

    def log(self, message, level=logging.info):
        name = self.get_description()
        level('[%s - %s] %s' % (
            name, self.parent_name, message
        ))

    def _load_validators(self):
        return load_classes(default=self.config.VALIDATORS)

    def _load_facters(self):
        return load_classes(default=self.config.FACTERS)

    def start_otto(self):
        self.info('Starting Octopus with %d concurrent threads.' % self.options.concurrency)
        self.otto = TornadoOctopus(
            concurrency=self.options.concurrency, cache=self.options.cache,
            connect_timeout_in_seconds=self.config.CONNECT_TIMEOUT_IN_SECONDS,
            request_timeout_in_seconds=self.config.REQUEST_TIMEOUT_IN_SECONDS
        )
        self.otto.start()

    def connect_sqlalchemy(self):
        autoflush = self.config.get('SQLALCHEMY_AUTO_FLUSH', False)
        connstr = self.config.SQLALCHEMY_CONNECTION_STRING
        engine = create_engine(
            connstr,
            convert_unicode=True,
            pool_size=self.config.SQLALCHEMY_POOL_SIZE,
            max_overflow=self.config.SQLALCHEMY_POOL_MAX_OVERFLOW,
            echo=self.options.verbose == 3
        )

        self.info("Connecting to \"%s\" using SQLAlchemy" % connstr)

        self.sqlalchemy_db_maker = sessionmaker(bind=engine, autoflush=autoflush, autocommit=True)
        self.db = scoped_session(self.sqlalchemy_db_maker)

    def connect_to_redis(self):
        host = self.config.get('REDISHOST')
        port = self.config.get('REDISPORT')

        self.info("Connecting to redis at %s:%d" % (host, port))
        self.redis = redis.StrictRedis(host=host, port=port, db=0)

        self.info("Connecting pubsub to redis at %s:%d" % (host, port))
        self.redis_pub_sub = redis.StrictRedis(host=host, port=port, db=0)

        self.cache = SyncCache(self.db, self.redis)

    def load_error_handlers(self):
        return load_classes(default=self.config.ERROR_HANDLERS)

    def handle_error(self, exc_type, exc_value, tb):
        for handler in self.error_handlers:
            handler.handle_exception(
                exc_type, exc_value, tb, extra={
                    'worker-uuid': self.uuid,
                    'holmes-version': __version__
                }
            )

    @property
    def proxies(self):
        proxies = None
        if self.config.HTTP_PROXY_HOST is not None:
            proxy = "%s:%s" % (self.config.HTTP_PROXY_HOST, self.config.HTTP_PROXY_PORT)
            http_proxy = proxy
            https_proxy = proxy

            proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }

        return proxies

    def async_get(self, url, handler, method='GET', **kw):
        url, response = self.cache.get_request(url)

        if not response:
            kw['proxy_host'] = self.config.HTTP_PROXY_HOST
            kw['proxy_port'] = self.config.HTTP_PROXY_PORT

            self.debug('Enqueueing %s for %s...' % (method, url))
            self.otto.enqueue(url, self.handle_response(url, handler), method, **kw)
        else:
            handler(url, response)

    def handle_response(self, url, handler):
        def handle(url, response):
            self.cache.set_request(
                url, response.status_code, response.headers, response.cookies,
                response.text, response.effective_url, response.error, response.request_time,
                self.config.REQUEST_CACHE_EXPIRATION_IN_SECONDS
            )
            handler(url, response)
        return handle

    def publish(self, data):
        self.redis_pub_sub.publish('events', data)

    def _insert_keys(self, keys):
        from holmes.models import Key

        with self.db.begin(subtransactions=True):
            for name in keys.keys():
                key = Key.get_or_create(self.db, name)
                keys[name]['key'] = key
                self.db.add(key)


class HolmesWorker(BaseWorker):
    def initialize(self):
        self.uuid = uuid4().hex
        self.working_url = None

        self.facters = self._load_facters()
        self.validators = self._load_validators()
        self.error_handlers = [handler(self.config) for handler in self.load_error_handlers()]

        self.start_otto()
        self.connect_sqlalchemy()
        self.connect_to_redis()

        self.facters = self._load_facters()
        self.validators = self._load_validators()

        self.fact_definitions = {}
        self.violation_definitions = {}

        for facter in self.facters:
            self.fact_definitions.update(facter.get_fact_definitions())

        self._insert_keys(self.fact_definitions)

        for validator in self.validators:
            self.violation_definitions.update(validator.get_violation_definitions())

        self._insert_keys(self.violation_definitions)

    def config_parser(self, parser):
        parser.add_argument(
            '--concurrency',
            '-t',
            type=int,
            default=10,
            help='Number of threads (or async http requests) to use for Octopus (doing GETs concurrently)'
        )

        parser.add_argument(
            '--cache', default=False, action='store_true',
            help='Whether http requests should be cached by Octopus.'
        )

    def get_description(self):
        return "%s%sholmes-worker%s (holmes-api v%s)" % (
            Fore.BLUE,
            Style.BRIGHT,
            Style.RESET_ALL,
            __version__
        )

    def get_config_class(self):
        return Config

    def do_work(self):
        if self._ping_api():
            err = None
            job = self._load_next_job()
            if job and self._start_job(job['url']):
                try:
                    self._start_reviewer(job=job)
                except InvalidReviewError:
                    err = str(sys.exc_info()[1])
                    logging.error("Fail to review %s: %s" % (job['url'], err))

                self._complete_job(error=err)
            elif job:
                self.debug('Could not start job for url "%s". Maybe other worker doing it?' % job['url'])

    def _start_reviewer(self, job):
        if job:
            self.debug('Starting Review for [%s]' % job['url'])
            reviewer = Reviewer(
                api_url=self.config.HOLMES_API_URL,
                page_uuid=job['page'],
                page_url=job['url'],
                page_score=job['score'],
                ping_method=self._ping_api,
                increase_lambda_tax_method=self._increase_lambda_tax,
                config=self.config,
                validators=self.validators,
                facters=self.facters,
                async_get=self.async_get,
                wait=self.otto.wait,
                wait_timeout=0,  # max time to wait for all requests to finish
                db=self.db,
                cache=self.cache,
                publish=self.publish,
                fact_definitions=self.fact_definitions,
                violation_definitions=self.violation_definitions
            )

            reviewer.review()

    def _increase_lambda_tax(self, tax):
        tax = float(tax)
        self.db.query(Settings).update({'lambda_score': Settings.lambda_score + tax})

    def _ping_api(self):
        self._remove_zombie_workers()

        worker = Worker.by_uuid(self.uuid, self.db)

        with self.db.begin(subtransactions=True):
            if worker:
                worker.last_ping = datetime.now()
                worker.current_url = self.working_url
            else:
                worker = Worker(uuid=self.uuid, current_url=self.working_url)
                self.db.add(worker)

        self.publish(dumps({
            'type': 'worker-status',
            'workerId': str(worker.uuid)
        }))

        return True

    def _remove_zombie_workers(self):
        self.db.flush()

        dt = datetime.now() - timedelta(seconds=self.config.ZOMBIE_WORKER_TIME)

        for i in range(3):
            try:
                with self.db.begin(subtransactions=True):
                    self.db.execute('DELETE FROM workers WHERE last_ping < :dt', {'dt': dt})
                break
            except OperationalError:
                err = sys.exc_info()[1]
                if 'Deadlock found' in str(err):
                    logging.error('Deadlock happened! Trying again (try number %d)! (Details: %s)' % (i, str(err)))
                else:
                    raise

    def _load_next_job(self):
        return Page.get_next_job(self.db, self.config.REVIEW_EXPIRATION_IN_SECONDS)

    def _start_job(self, url):
        self.working_url = url

        worker = Worker.by_uuid(self.uuid, self.db)

        with self.db.begin(subtransactions=True):
            worker.current_url = url
            worker.last_ping = datetime.now()

        return True

    def _complete_job(self, error=None):
        self.working_url = None
        worker = Worker.by_uuid(self.uuid, self.db)

        if worker:
            for i in range(3):
                try:
                    with self.db.begin(subtransactions=True):
                        worker.current_url = None
                        worker.last_ping = datetime.now()
                    break
                except Exception:
                    err = sys.exc_info()[1]
                    logging.error('Deadlock detected... Try number %d. Error: %s' % (i, str(err)))

        return True


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
