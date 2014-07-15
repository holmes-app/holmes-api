#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tornado.gen import coroutine

from holmes.handlers import BaseHandler
from holmes.models import User


class UserLocaleHandler(BaseHandler):

    @coroutine
    def get(self):
        user = self.get_authenticated_user()

        if not user:
            return

        self.write_json({'locale': user.locale})
        self.finish()

    @coroutine
    def post(self):
        user = self.get_authenticated_user()

        if not user:
            return

        post_data = loads(self.request.body)
        locale = post_data.get('locale', None)

        if locale:
            User.update_locale(self.db, user, locale)

        self.write_json(self._('OK'))
        self.finish()
