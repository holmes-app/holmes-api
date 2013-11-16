#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from uuid import uuid4
from os.path import abspath, dirname, join

import requests
from ujson import dumps, loads
from requests.exceptions import ConnectionError
from sheep import Shepherd
from colorama import Fore, Style

from holmes import __version__
from holmes.config import Config
from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.utils import load_classes


class HolmesWorker(Shepherd):
    def initialize(self):
        self.root_path = abspath(join(dirname(__file__), '..'))
        self.uuid = None
        self.working = True

        self.facters = self._load_facters()
        self.validators = self._load_validators()

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

    def get(self, url):
        url = join(self.config.HOLMES_API_URL.rstrip('/'), url.lstrip('/'))
        return requests.get(url, proxies=self.proxies)

    def post(self, url, data={}):
        url = join(self.config.HOLMES_API_URL.rstrip('/'), url.lstrip('/'))
        return requests.post(url, data=data, proxies=self.proxies)

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
        if self.uuid is None:
            self.uuid = uuid4().hex

        if self._ping_api():
            err = None
            job = self._load_next_job()
            if job:
                #self._start_job(job['review'])

                try:
                    self._start_reviewer(job=job)
                except InvalidReviewError:
                    err = str(sys.exc_info()[1])
                    logging.error("Fail to review %s: %s" % (job['url'], err))

                #self._complete_job(job['review'], error=err)

    def _start_reviewer(self, job):
        if job:
            logging.debug('Starting Review for [%s]' % job['url'])
            reviewer = Reviewer(
                api_url=self.config.HOLMES_API_URL,
                page_uuid=job['page'],
                page_url=job['url'],
                config=self.config,
                validators=self.validators,
                facters=self.facters
            )

            reviewer.review()

    def _ping_api(self):
        try:
            self.post('/worker/%s/alive' % self.uuid, data={'worker_uuid': self.uuid})
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

    def _start_job(self, review_uuid):
        if not review_uuid:
            return False

        try:
            response = self.post('/worker/%s/review/%s/start' % (self.uuid, review_uuid))
            return ('OK' == response.text)

        except ConnectionError:
            logging.error('Fail to start review.')

    def _complete_job(self, review_uuid, error=None):
        if not review_uuid:
            return False

        try:
            url = '/worker/%s/review/%s/complete' % (self.uuid, review_uuid)
            response = self.post(url, data=dumps({'error': error}))
            return ('OK' == response.text)
        except ConnectionError:
            logging.error('Fail to complete worker.')

    def _load_validators(self):
        return load_classes(default=self.config.VALIDATORS)

    def _load_facters(self):
        return load_classes(default=self.config.FACTERS)


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
