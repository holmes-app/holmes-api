#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class RobotsFacter(Facter):

    def get_facts(self):
        if not self.reviewer.is_root():
            return

        url = self.rebase('/robots.txt')

        self.review.data['robots.response'] = None

        self.async_get(url, self.handle_robots_loaded)

    def handle_robots_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))

        if url == self.rebase('/robots.txt') and response.status_code <= 399:
            self.add_fact(
                key='robots.url',
                value=url,
                title='Robots',
                unit='robots'
            )

        self.review.data['robots.response'] = response
