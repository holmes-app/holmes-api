#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.gen import coroutine
from tornado import gen
from ujson import loads

from holmes.models import Domain, DomainsViolationsPrefs, User
from holmes.handlers import BaseHandler


class DomainsViolationsPrefsHandler(BaseHandler):

    @coroutine
    def options(self, domain_name=None):
        super(DomainsViolationsPrefsHandler, self).options()

    @coroutine
    def get(self, domain_name):
        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        prefs = DomainsViolationsPrefs.get_domains_violations_prefs_by_domain(
            self.db, domain.name
        )

        violation_defs = self.application.violation_definitions

        result = []

        for pref in prefs:
            key = violation_defs.get(pref.get('key'))

            if key is None:
                continue

            result.append({
                'key': pref.get('key'),
                'title': key.get('default_value_description', None),
                'category': key.get('category', None),
                'value': pref.get('value'),
                'default_value': key.get('default_value', None),
                'unit': key.get('unit', None)
            })

        self.write_json(result)

    @gen.coroutine
    def post(self, domain_name):
        access_token = self.request.headers.get('X-AUTH-HOLMES', None)

        if self.is_empty_access_token(access_token):
            return

        result = yield User.authenticate(access_token, self.application)

        if self.is_unauthorized_user(result):
            return

        domain = Domain.get_domain_by_name(domain_name, self.db)

        if not domain:
            self.set_status(404, self._('Domain %s not found') % domain_name)
            return

        post_data = loads(self.request.body)

        DomainsViolationsPrefs.update_by_domain(
            self.db, self.cache, domain, post_data
        )

        self.write_json({
            'reason': self._('Preferences successfully saved!'),
            'description': self._('Preferences successfully saved!')
        })
