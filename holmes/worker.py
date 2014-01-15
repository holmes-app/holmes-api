#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from uuid import uuid4
from os.path import join

import requests
from ujson import dumps, loads
from requests.exceptions import ConnectionError
from sheep import Shepherd
from colorama import Fore, Style
from octopus import TornadoOctopus

from holmes import __version__
from holmes.config import Config
from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.utils import load_classes


class HolmesWorker(Shepherd):
    def initialize(self):
        self.uuid = uuid4().hex
        self.working = True

        self.facters = self._load_facters()
        self.validators = self._load_validators()
        self.error_handlers = [handler(self.config) for handler in self._load_error_handlers()]

        logging.debug('Starting Octopus with %d concurrent threads.' % self.options.concurrency)
        self.otto = TornadoOctopus(
            concurrency=self.options.concurrency, cache=self.options.cache,
            connect_timeout_in_seconds=self.config.CONNECT_TIMEOUT_IN_SECONDS,
            request_timeout_in_seconds=self.config.REQUEST_TIMEOUT_IN_SECONDS
        )
        self.otto.start()

    def _load_error_handlers(self):
        return load_classes(default=self.config.ERROR_HANDLERS)

    def handle_error(self, exc_type, exc_value, tb):
        for handler in self.error_handlers:
            handler.handle_exception(
                exc_type, exc_value, tb, extra={
                    'worker-uuid': self.uuid,
                    'holmes-version': __version__
                }
            )

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

    def tornado_async_get(self, url, handler, method='GET', **kw):
        #if self.proxies:
            #kw['proxies'] = self.proxies

        kw['proxy_host'] = self.config.HTTP_PROXY_HOST
        kw['proxy_port'] = self.config.HTTP_PROXY_PORT

        logging.debug('Enqueueing %s for %s...' % (method, url))
        self.otto.enqueue(url, handler, method, **kw)

    def async_get(self, url, handler, method='GET', **kw):
        if self.proxies:
            kw['proxies'] = self.proxies

        logging.debug('Enqueueing %s for %s...' % (method, url))
        self.otto.enqueue(url, handler, method, **kw)

    def get(self, url):
        url = join(self.config.HOLMES_API_URL.rstrip('/'), url.lstrip('/'))
        return requests.get(url)

    def post(self, url, data={}):
        url = join(self.config.HOLMES_API_URL.rstrip('/'), url.lstrip('/'))
        return requests.post(url, data=data)

    def get_description(self):
        return "%s%sholmes-worker%s (holmes-api v%s)" % (
            Fore.BLUE,
            Style.BRIGHT,
            Style.RESET_ALL,
            __version__
        )

    def get_config_class(self):
        return Config

    def stop_work(self):
        try:
            self.post('/worker/%s/dead' % self.uuid, data={'worker_uuid': self.uuid})
        except ConnectionError:
            pass
        self.working = False

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
                logging.debug('Could not start job for url "%s". Maybe other worker doing it?' % job['url'])

    def _start_reviewer(self, job):
        if job:
            logging.debug('Starting Review for [%s]' % job['url'])
            reviewer = Reviewer(
                api_url=self.config.HOLMES_API_URL,
                page_uuid=job['page'],
                page_url=job['url'],
                page_score=job['score'],
                config=self.config,
                validators=self.validators,
                facters=self.facters,
                async_get=self.tornado_async_get,
                wait=self.otto.wait,
                wait_timeout=0  # max time to wait for all requests to finish
            )

            reviewer.review()

    def _ping_api(self):
        try:
            self.post('/worker/%s/alive' % self.uuid)
            return True
        except ConnectionError:
            logging.fatal('Fail to ping API [%s]. Stopping Worker.' % self.config.HOLMES_API_URL)
            self.stop_work()
            return False

    def _load_next_job(self):
        try:
            response = self.get('/next')
            if response and response.text:
                return loads(response.text)
        except ConnectionError:
            logging.fatal('Fail to get next review from [%s]. Stopping Worker.' % self.config.HOLMES_API_URL)
            self.stop_work()

        return None

    def _start_job(self, url):
        if not url:
            return False

        try:
            response = self.post('/worker/%s/start' % self.uuid, data=url)
            if response.text == 'OK':
                return True

            if response.text == 'NOK':
                logging.debug('Failed to acquire lock on %s.' % url)
                return False
        except ConnectionError:
            err = sys.exc_info()
            logging.error('Fail to start review: %s.' % err[1])

        return False

    def _complete_job(self, error=None):
        try:
            url = '/worker/%s/complete' % self.uuid
            response = self.post(url, data=dumps({'error': error}))
            return ('OK' == response.text)
        except ConnectionError:
            logging.error('Fail to complete worker.')

        return False

    def _load_validators(self):
        return load_classes(default=self.config.VALIDATORS)

    def _load_facters(self):
        return load_classes(default=self.config.FACTERS)


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
