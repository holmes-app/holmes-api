#!/usr/bin/python
# -*- coding: utf-8 -*-

import pkgutil
import pkg_resources

from raven import Client


def get_modules():
    resolved = {}
    modules = [mod[1] for mod in tuple(pkgutil.iter_modules())]
    for module in modules:
        try:
            res_mod = pkg_resources.get_distribution(module)
            if res_mod is not None:
                resolved[module] = res_mod.version
        except pkg_resources.DistributionNotFound:
            pass

    return resolved


class SentryErrorHandler(object):
    def __init__(self, config):
        self.config = config

        if self.config.USE_SENTRY:
            self.sentry = Client(self.config.SENTRY_DSN_URL)

        self.modules = get_modules()

    def handle_exception(self, typ, value, tb, extra={}):
        if self.config.USE_SENTRY:
            self.sentry.captureException(
                (typ, value, tb),
                extra=extra,
                data={
                    'modules': self.modules
                }
            )
