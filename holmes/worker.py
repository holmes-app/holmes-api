#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4
from datetime import datetime, timedelta

from ujson import dumps
from colorama import Fore, Style
from octopus import TornadoOctopus
from octopus.limiter.redis.per_domain import Limiter

from holmes import __version__
from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.utils import load_classes, count_url_levels, get_domain_from_url
from holmes.models import Page, Domain
from holmes.models import Limiter as LimiterModel
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
        domains = self.cache.get_domain_limiters()

        if hasattr(self.otto, 'limiter') and self.otto.limiter is not None:
            self.otto.limiter.update_domain_definitions(*domains)

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
            key = Key.get_or_create(self.db, name)
            keys[name]['key'] = key
            self.db.add(key)


class HolmesWorker(BaseWorker):
    def initialize(self):
        self.uuid = uuid4().hex
        self.working_url = None
        self.domain_name = None
        self.last_ping = None

        self.facters = self._load_facters()
        self.validators = self._load_validators()
        self.error_handlers = [handler(self.config) for handler in self.load_error_handlers()]

        self.connect_sqlalchemy()
        self.connect_to_redis()
        self.start_otto()

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
        uuid = str(getattr(self, 'uuid', ''))

        return "%s%sholmes-worker-%s%s" % (
            Fore.BLUE,
            Style.BRIGHT,
            uuid,
            Style.RESET_ALL,
        )

    def do_work(self):
        errored = False
        try:
            self.debug('Started doing work...')

            err = None
            job = self._load_next_job()

            if job and self._start_job(job['url']):
                try:
                    self.info('Starting new job for %s...' % job['url'])
                    self._start_reviewer(job=job)
                except InvalidReviewError:
                    errored = True
                    err = str(sys.exc_info()[1])
                    self.error("Fail to review %s: %s" % (job['url'], err))
                    self.db.rollback()

                lock = job.get('lock', None)
                self._complete_job(lock, error=err)

            elif job:
                self.debug('Could not start job for url "%s". Maybe other worker doing it?' % job['url'])

            if not errored:
                self.db.commit()
        except Exception:
            err = str(sys.exc_info()[1])
            self.error("Fail to complete work: %s" % err)
            self.db.rollback()

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

    def _ping_api(self):
        self.debug('Pinging that this worker is still alive...')

        self.last_ping = datetime.utcnow()

        self.publish(dumps({
            'type': 'worker-status',
            'workerId': str(self.uuid),
            'dt': self.last_ping,
            'url': self.working_url,
            'domainName': self.domain_name,
        }))

    def handle_limiter_miss(self, url):
        self.working_url = url

        if self.last_ping < datetime.utcnow() - timedelta(seconds=1):
            self._ping_api()

    def _load_next_job(self):
        return Page.get_next_job(
            self.db,
            self.config.WORKERS_LOOK_AHEAD_PAGES,
            self.config.REVIEW_EXPIRATION_IN_SECONDS,
            self.cache,
            self.config.NEXT_JOB_URL_LOCK_EXPIRATION_IN_SECONDS)

    def _start_job(self, url):
        self.update_otto_limiter()
        if not self._verify_workers_limits(url):
            return False

        self.working_url = url

        if self.working_url:
            self.domain_name, _ = get_domain_from_url(self.working_url)

        self._ping_api()

        return True

    def _verify_workers_limits(self, url, avg_links_per_page=10):
        active_domains = Domain.get_active_domains(self.db)
        return LimiterModel.has_limit_to_work(self.db, self.cache, active_domains, url, avg_links_per_page)

    def _complete_job(self, lock, error=None):
        self.working_url = None
        self.domain_name = None
        self._ping_api()

def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
