#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from datetime import datetime, timedelta

from ujson import dumps
from colorama import Fore, Style
from octopus import TornadoOctopus
from octopus.limiter.redis.per_domain import Limiter
from sqlalchemy.exc import OperationalError

from holmes import __version__
from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.utils import load_classes, count_url_levels
from holmes.models import Settings, Worker, Page
from holmes.cli import BaseCLI


class BaseWorker(BaseCLI):
    def _load_validators(self):
        return load_classes(default=self.config.VALIDATORS)

    def _load_facters(self):
        return load_classes(default=self.config.FACTERS)

    def get_otto_limiter(self):
        domains = self.cache.get_domain_limiters()
        limiter = None

        if domains:
            limiter = Limiter(
                *domains,
                redis=self.redis,
                expiration_in_seconds=self.config.LIMITER_LOCKS_EXPIRATION
            )

            limiter.subscribe_to_lock_miss(self.handle_limiter_miss)

        return limiter

    def update_otto_limiter(self):
        self.otto.limiter = self.get_otto_limiter()

    def start_otto(self):
        self.info('Starting Octopus with %d concurrent threads.' % self.options.concurrency)
        self.otto = TornadoOctopus(
            concurrency=self.options.concurrency, cache=self.options.cache,
            connect_timeout_in_seconds=self.config.CONNECT_TIMEOUT_IN_SECONDS,
            request_timeout_in_seconds=self.config.REQUEST_TIMEOUT_IN_SECONDS,
            limiter=self.get_otto_limiter()
        )
        self.otto.start()

    def handle_error(self, exc_type, exc_value, tb):
        for handler in self.error_handlers:
            handler.handle_exception(
                exc_type, exc_value, tb, extra={
                    'worker-uuid': self.uuid,
                    'holmes-version': __version__
                }
            )

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

    def handle_limiter_miss(self, url):
        pass

    def publish(self, data):
        self.redis_pub_sub.publish('events', data)

    def _insert_keys(self, keys):
        from holmes.models import Key

        for name in keys.keys():
            self.db.begin(subtransactions=True)
            key = Key.get_or_create(self.db, name)
            keys[name]['key'] = key
            self.db.add(key)
            self.db.commit()


class HolmesWorker(BaseWorker):
    def initialize(self):
        self.uuid = uuid4().hex
        self.working_url = None

        self.facters = self._load_facters()
        self.validators = self._load_validators()
        self.error_handlers = [handler(self.config) for handler in self.load_error_handlers()]

        self.connect_sqlalchemy()
        self.connect_to_redis()
        self.start_otto()

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

    def do_work(self):
        if self._ping_api():
            err = None
            job = self._load_next_job()
            if job and self._start_job(job['url']):
                try:
                    self._start_reviewer(job=job)
                except InvalidReviewError:
                    err = str(sys.exc_info()[1])
                    self.error("Fail to review %s: %s" % (job['url'], err))

                lock = job.get('lock', None)
                self._complete_job(lock, error=err)
            elif job:
                self.debug('Could not start job for url "%s". Maybe other worker doing it?' % job['url'])

    def _start_reviewer(self, job):
        if job:

            if count_url_levels(job['url']) > self.config.MAX_URL_LEVELS:
                self.info('Max URL levels! Details: %s' % job['url'])
                return

            self.debug('Starting Review for [%s]' % job['url'])
            reviewer = Reviewer(
                api_url=self.config.HOLMES_API_URL,
                page_uuid=job['page'],
                page_url=job['url'],
                page_score=job['score'],
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
        for i in range(3):
            self.db.begin(subtransactions=True)
            try:
                self.db.query(Settings).update({'lambda_score': Settings.lambda_score + tax})
                self.db.commit()
                break
            except Exception:
                err = sys.exc_info()[1]
                if 'Deadlock found' in str(err):
                    self.error('Deadlock happened! Trying again (try number %d)! (Details: %s)' % (i, str(err)))
                else:
                    self.db.rollback()
                    raise

    def _ping_api(self):
        self._remove_zombie_workers()

        worker = Worker.by_uuid(self.uuid, self.db)

        self.db.begin(subtransactions=True)

        try:
            if worker:
                worker.last_ping = datetime.utcnow()
                worker.current_url = self.working_url
            else:
                worker = Worker(uuid=self.uuid, current_url=self.working_url)
                self.db.add(worker)
            self.db.flush()
            self.db.commit()
        except OperationalError:
            exc = sys.exc_info()[1]
            self.db.rollback()
            self.error("Could not ping API due to error: %s" % str(exc))
            return False

        self.publish(dumps({
            'type': 'worker-status',
            'workerId': str(worker.uuid)
        }))

        return True

    def handle_limiter_miss(self, url):
        self._ping_api()

    def _remove_zombie_workers(self):
        self.db.flush()

        dt = datetime.utcnow() - timedelta(seconds=self.config.ZOMBIE_WORKER_TIME)

        for i in range(3):
            self.db.begin(subtransactions=True)

            try:
                self.db.execute('DELETE FROM workers WHERE last_ping < :dt', {'dt': dt})
                self.db.flush()
                self.db.commit()
                break
            except Exception:
                err = sys.exc_info()[1]
                if 'Deadlock found' in str(err):
                    self.error('Deadlock happened! Trying again (try number %d)! (Details: %s)' % (i, str(err)))
                else:
                    self.db.rollback()
                    raise

    def _load_next_job(self):
        return Page.get_next_job(
            self.db,
            self.config.REVIEW_EXPIRATION_IN_SECONDS,
            self.cache,
            self.config.NEXT_JOB_URL_LOCK_EXPIRATION_IN_SECONDS)

    def _start_job(self, url):
        self.update_otto_limiter()

        self.working_url = url

        self.db.begin(subtransactions=True)
        worker = Worker.by_uuid(self.uuid, self.db)
        worker.current_url = url
        worker.last_ping = datetime.utcnow()
        self.db.flush()
        self.db.commit()

        return True

    def _complete_job(self, lock, error=None):
        self.working_url = None
        worker = Worker.by_uuid(self.uuid, self.db)

        if worker:
            for i in range(3):
                self.db.begin(subtransactions=True)

                try:
                    self.cache.release_next_job(lock)
                    worker.current_url = None
                    worker.last_ping = datetime.utcnow()
                    self.db.flush()
                    self.db.commit()
                    break
                except Exception:
                    err = sys.exc_info()[1]
                    if 'Deadlock found' in str(err):
                        self.error('Deadlock happened! Trying again (try number %d)! (Details: %s)' % (i, str(err)))
                    else:
                        self.db.rollback()
                        raise

        return True


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
