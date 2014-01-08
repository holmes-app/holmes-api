#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from os.path import join
import urlparse
import inspect
import email.utils as eut
from datetime import datetime

import codecs
from box.util.rotunicode import RotUnicode
codecs.register(RotUnicode.search_function)

import requests
from requests.exceptions import ConnectionError
import lxml.html
import logging
from ujson import dumps

from holmes.config import Config
from holmes.facters import Facter
from holmes.validators.base import Validator


class InvalidReviewError(RuntimeError):
    pass


class ReviewDAO(object):
    def __init__(self, page_uuid, page_url, last_modified=None, expires=None):
        self.page_uuid = page_uuid
        self.page_url = page_url
        self.last_modified = last_modified
        self.expires = expires
        self.facts = {}
        self.violations = []
        self.data = {}
        self._current = None

    def add_fact(self, key, value):
        self.facts[key] = {
            'key': key,
            'value': value
        }

    def add_violation(self, key, value, points):
        self.violations.append({
            'key': key,
            'value': value,
            'points': points
        })

    def to_dict(self):
        return {
            'page_uuid': self.page_uuid,
            'page_url': self.page_url,
            'facts': self.facts.values(),
            'violations': self.violations,
            'lastModified': self.last_modified,
            'expires': self.expires
        }


class Reviewer(object):
    def __init__(self, api_url, page_uuid, page_url, config=None, validators=[], facters=[], async_get=None, wait=None, wait_timeout=None):
        self.api_url = api_url

        self.page_uuid = page_uuid
        self.page_url = page_url

        self.review_dao = ReviewDAO(self.page_uuid, self.page_url)

        assert isinstance(config, Config), 'config argument must be an instance of holmes.config.Config'
        self.config = config

        for facter in facters:
            message = 'All facters must subclass holmes.facters.Facter (Error: %s)' % facter.__class__.__name__
            assert inspect.isclass(facter), message
            assert issubclass(facter, Facter), message

        for validator in validators:
            message = 'All validators must subclass holmes.validators.base.Validator (Error: %s)' % validator.__class__.__name__
            assert inspect.isclass(validator), message
            assert issubclass(validator, Validator), message

        self.validators = validators
        self.facters = facters

        self.responses = {}
        self.raw_responses = {}
        self.status_codes = {}

        self.proxies = None
        if self.config.HTTP_PROXY_HOST is not None:
            proxy = "%s:%s" % (self.config.HTTP_PROXY_HOST, self.config.HTTP_PROXY_PORT)
            http_proxy = proxy
            https_proxy = proxy

            self.proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }

        self.async_get_func = async_get
        self._wait_for_async_requests = wait
        self._wait_timeout = wait_timeout

    def _async_get(self, url, handler, method='GET', **kw):
        if self.async_get_func:
            self.async_get_func(url, handler, method, **kw)

    def _get(self, url):
        #if self.proxies:
            #logging.debug('Getting "%s" using proxy "%s"...' % (url, self.proxies.get('http', None)))
            #return requests.get(url, proxies=self.proxies)

        return requests.get(url)

    def _post(self, url, data):
        #if self.proxies:
            #logging.debug('Posting to "%s" using proxy "%s"...' % (url, self.proxies.get('http', None)))
            #return requests.post(url, data=data, proxies=self.proxies)

        return requests.post(url, data=data)

    def review(self):
        self.load_content(self.content_loaded)
        self.wait_for_async_requests()

    def load_content(self, callback):
        self._async_get(self.page_url, callback)

    def content_loaded(self, url, response):
        if response.status_code > 399:
            if response.text:
                text = response.text.decode('rotunicode')
            else:
                text = 'Empty response.text'

            msg = "Could not load '%s' (%s) - %s!" % (url,
                                                      response.status_code,
                                                      text)
            logging.error(msg)
            return

        logging.debug('Content for url %s loaded.' % url)

        last_modified = None

        if 'Last-Modified' in response.headers:
            last_modified = datetime(*eut.parsedate(response.headers['Last-Modified'])[:6])

        self.review_dao.last_modified = last_modified

        expires = None
        if 'Expires' in response.headers:
            expires = datetime(*eut.parsedate(response.headers['Expires'])[:6])

        self.review_dao.expires = expires

        self._current = response

        try:
            self._current.html = lxml.html.fromstring(response.text)
        except (lxml.etree.XMLSyntaxError, lxml.etree.ParserError):
            self._current.html = None

            # can't do this there, this is not a validator
            #self.add_violation(
                #key='invalid.content',
                #title='Invalid Content',
                #description='Fail to parse content from %s' % url,
                #points=1000)

        self.run_facters()
        self.wait_for_async_requests()

        self.run_validators()
        self.wait_for_async_requests()

        self.save_review()

    @property
    def current(self):
        return self._current

    @property
    def current_html(self):
        if not hasattr(self.current, 'html') or self.current.html is None:
            return lxml.html.HtmlElement()
        else:
            return self.current.html

    def run_facters(self):
        for facter in self.facters:
            logging.debug('---------- Started running facter %s ---------' % facter.__name__)
            facter_instance = facter(self)
            facter_instance.get_facts()

    def run_validators(self):
        for validator in self.validators:
            logging.debug('---------- Started running validator %s ---------' % validator.__name__)
            validator_instance = validator(self)
            validator_instance.validate()

    def get_url(self, url):
        return join(self.api_url.rstrip('/'), url.lstrip('/'))

    def enqueue(self, urls):
        if not urls:
            return

        if isinstance(urls, basestring):
            post_url = self.get_url('/page')
            data = dumps({
                'url': urls,
                'origin_uuid': str(self.page_uuid)
            })
            error_message = "Could not enqueue page '" + urls + "'! Status Code: %d, Error: %s"
        else:
            post_url = self.get_url('/pages')
            data = {
                "url": urls,
                'origin_uuid': str(self.page_uuid)
            }
            error_message = "Could not enqueue the " + str(len(urls)) + " pages sent! Status Code: %d, Error: %s"

        response = self._post(post_url, data=data)

        if response.status_code > 399:
            logging.error(error_message % (
                response.status_code,
                response.text
            ))

    def add_fact(self, key, value):
        self.review_dao.add_fact(key, value)

    def add_violation(self, key, value, points):
        self.review_dao.add_violation(key, value, points)

    def save_review(self):
        url = self.get_url('/page/%s/review/' % (self.page_uuid))

        try:
            data = dumps(self.review_dao.to_dict())
            response = self._post(url, data={
                'review': data
            })
        except ConnectionError:
            err = sys.exc_info()[1]
            logging.error("Could not save review! ConnectionError - %s (%s)" % (
                url,
                str(err)
            ))
            return

        if response.status_code > 399:
            logging.error("Could not save review! Status Code: %d, Error: %s" % (
                response.status_code,
                response.text
            ))

    def wait_for_async_requests(self):
        self._wait_for_async_requests(self._wait_timeout)

    def is_root(self):
        result = urlparse.urlparse(self.page_url)
        return '{0}://{1}'.format(result.scheme, result.netloc) == self.page_url.rstrip('/')
