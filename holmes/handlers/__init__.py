#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from ujson import dumps
from tornado.web import RequestHandler

from holmes import __version__
from holmes.models import User
import holmes.utils as utils


class BaseHandler(RequestHandler):

    @property
    def config(self):
        return self.application.config

    def initialize(self, *args, **kw):
        self.is_public = kw.pop('is_public', False)
        super(BaseHandler, self).initialize(*args, **kw)

        locale = self.get_browser_locale()
        self._ = utils.install_i18n(locale.code)
        self.jwt = utils.Jwt(self.config.SECRET_KEY)

    def get_authenticated_user(self):
        authenticated, payload = self.is_authenticated()
        if authenticated:
            user_email = payload['sub']
            user = User.by_email(user_email, self.db)
            return user
        else:
            return None

    def validate_superuser(self):
        user = self.get_authenticated_user()
        if not user or not user.is_superuser:
            self.set_unauthorized()
            return False
        return True

    def set_unauthorized(self):
        self.set_status(401)
        self.write('Unauthorized')
        self.finish()

    def renew_authentication(self, payload):
        payload.update(dict(
            iat=datetime.utcnow(),
            exp=datetime.utcnow() + timedelta(
                seconds=self.config.SESSION_EXPIRATION
            )
        ))
        token = self.jwt.encode(payload)
        self.set_cookie('HOLMES_AUTH_TOKEN', token)

    def is_authenticated(self):
        return self.jwt.try_to_decode(self.get_cookie('HOLMES_AUTH_TOKEN'))

    def authenticate_request(self):
        authenticated, payload = self.is_authenticated()
        if authenticated:
            self.renew_authentication(payload)
        else:
            self.set_unauthorized()

    def prepare(self):
        if self.request.method != 'OPTIONS' and not self.is_public:
            self.authenticate_request()

    def log_exception(self, typ, value, tb):
        for handler in self.application.error_handlers:
            handler.handle_exception(
                typ, value, tb, extra={
                    'url': self.request.full_url(),
                    'ip': self.request.remote_ip,
                    'holmes-version': __version__
                }
            )

        super(BaseHandler, self).log_exception(typ, value, tb)

    def on_finish(self):
        if self.application.config.COMMIT_ON_REQUEST_END:
            if self.get_status() > 399:
                logging.debug('ROLLING BACK TRANSACTION')
                self.db.rollback()
            else:
                logging.debug('COMMITTING TRANSACTION')
                self.db.flush()
                self.db.commit()
                self.application.event_bus.flush()

    def options(self, *args):
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        self.set_header(
            'Access-Control-Allow-Origin',
            self.application.config.HOLMES_WEB_URL
        )
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS'
        )
        self.set_header('Access-Control-Allow-Headers', 'Accept, Content-Type')

    def write_json(self, obj):
        self.set_header("Content-Type", "application/json")
        self.write(dumps(obj))

    @property
    def cache(self):
        return self.application.cache

    @property
    def db(self):
        return self.application.db

    @property
    def girl(self):
        return self.application.girl
