#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class RobotsFacter(Facter):

    def get_facts(self):
        url = self.rebase('/robots.txt')

        self.review.data['robots.response'] = None

        self.add_fact(
            key='robots.url',
            value=url,
            title='Robots',
            unit='robots'
        )

        self.async_get(url, self.handle_robots_loaded)

    def handle_robots_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))
        self.review.data['robots.response'] = response
