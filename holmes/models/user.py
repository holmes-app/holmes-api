#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import sqlalchemy as sa
from ujson import loads
import datetime
from tornado.concurrent import return_future

from holmes.models import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    fullname = sa.Column('fullname', sa.String(200), nullable=False)
    email = sa.Column('email', sa.String(100), nullable=False, unique=True)
    is_superuser = sa.Column(
        'is_superuser',
        sa.Boolean,
        nullable=False,
        default=False
    )
    last_login = sa.Column('last_login', sa.DateTime, nullable=True)

    def to_dict(self):
        return {
            'fullname': self.fullname,
            'email': self.email,
            'is_superuser': bool(self.is_superuser),
            'last_login': self.last_login
        }

    def __str__(self):
        return str(self.email)

    def __repr__(self):
        return str(self)

    @classmethod
    def by_email(cls, email, db):
        return db.query(User).filter(User.email == email).first()

    @classmethod
    @return_future
    def authenticate(cls, access_token, fetch_method, db, config, callback):
        logging.info('Authenticating...')

        google_api_url = 'https://www.googleapis.com/oauth2/v1/tokeninfo'
        url = '%s?access_token=%s' % (google_api_url, access_token)

        fetch_method(
            url,
            cls.handle_authenticate(cls.handle_authorize(db, config, callback)),
            proxy_host=config.HTTP_PROXY_HOST,
            proxy_port=config.HTTP_PROXY_PORT
        )

    @classmethod
    def handle_authenticate(cls, callback):
        def handle(*args, **kw):
            response = args[-1]
            callback(response.code, response.body)
        return handle

    @classmethod
    def handle_authorize(cls, db, config, callback):
        def handle(code, body):
            if code > 399:
                callback(({
                    'reason': 'Error',
                    'status': code,
                    'details': body
                }))
                return

            data = loads(body)

            # Verify that the access token is valid for this app.
            if data.get('issued_to') != config.GOOGLE_CLIENT_ID:
                callback({
                    'status': 401,
                    'reason': "Token's client ID does not match app's.",
                })
                return

            user_email = data.get('email')

            from holmes.models import User

            user = User.by_email(user_email, db)
            if user:
                user.last_login = datetime.datetime.now()
                db.flush()
                db.commit()
                callback({
                    'status': 200,
                    'user': user.to_dict()
                })
                return

            callback({
                'status': 403,
                'reason': 'Unauthorized user'
            })
            return

        return handle
