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


class HolmesWorker(Shepherd):
    def __init__(self, *args, **kw):
        super(HolmesWorker, self).__init__(*args, **kw)

        self.root_path = abspath(join(dirname(__file__), '..'))
        self.uuid = uuid4().hex
        self.working = True

        self.validators = self._load_validators()

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
            if job:
                self._start_job(job['review'])

                try:
                    self._start_reviewer(job=job)
                except InvalidReviewError:
                    err = str(sys.exc_info()[1])
                    logging.error("Fail to review %s: %s" % (job['url'], err))

                self._complete_job(job['review'], error=err)

    def _start_reviewer(self, job):
        if job:
            logging.debug('Starting Review for [%s]' % job['url'])
            reviewer = Reviewer(
                api_url=self.config.HOLMES_API_URL,
                page_uuid=job['page'],
                page_url=job['url'],
                review_uuid=job['review'],
                config=self.config,
                validators=self.validators
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
            response = self.post('/next')
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

    def _load_validators(self, validators=None, validators_to_load=None):
        if validators_to_load is None:
            validators_to_load = self.config.VALIDATORS

        if validators is None:
            validators = []

        for validator_full_name in validators_to_load:
            if isinstance(validator_full_name, (tuple, set, list)):
                self._load_validators(validators, validator_full_name)
                continue

            try:
                module_name, class_name = validator_full_name.rsplit('.', 1)
                module = __import__(module_name, globals(), locals(), class_name)
                validators.append(getattr(module, class_name))
            except ValueError:
                logging.warn('Invalid validator name [%s]. Will be ignored.' % validator_full_name)
            except AttributeError:
                logging.warn('Validator [%s] not found. Will be ignored.' % validator_full_name)
            except ImportError:
                logging.warn('Module [%s] not found. Will be ignored.' % validator_full_name)

        return validators


def main():
    worker = HolmesWorker(sys.argv[1:])
    worker.run()

if __name__ == '__main__':
    main()
