#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tornado.gen import coroutine

from holmes.models import Limiter, User
from holmes.handlers import BaseHandler


class LimiterHandler(BaseHandler):
    @coroutine
    def options(self, id=None):
        super(LimiterHandler, self).options()

    @coroutine
    def get(self):

        limiters = Limiter.get_all(
            self.db, domain_filter=self.get_argument('domain_filter', None)
        )

        result = []

        for limit in limiters:
            current_value = yield self.cache.get_limit_usage(limit.url) or 0

            percentage = 0
            if limit.value > 0:
                percentage = float(current_value) / limit.value

            result.append({
                'id': limit.id,
                'url': limit.url,
                'currentValue': current_value,
                'maxValue': limit.value or 0,
                'concurrentRequestsPercentage': percentage
            })

        self.write_json(result)

    @coroutine
    def post(self):
        access_token = self.request.headers.get('X-AUTH-HOLMES', None)

        if access_token is None:
            self.set_status(403)
            self.write_json({'reason': 'Empty access token', 'description': self._('Empty access token')})
            return

        result = yield User.authenticate(
            access_token,
            self.application.http_client.fetch,
            self.db,
            self.application.config
        )

        if result and result.get('user', None) is None:
            self.set_status(401)
            self.write_json({'reason': 'Unauthorized user', 'description': self._('Unauthorized user')})
            return

        post_data = loads(self.request.body)
        url = post_data.get('url', None)
        connections = self.application.config.DEFAULT_NUMBER_OF_CONCURRENT_CONNECTIONS
        value = post_data.get('value', connections)

        if not url and not value:
            self.set_status(400)
            self.write_json({'reason': 'Not url or value', 'description': self._('Not url or value')})
            return

        result = Limiter.add_or_update_limiter(self.db, url, value)

        yield self.cache.remove_domain_limiters_key()

        self.write_json(result)

    @coroutine
    def delete(self, limiter_id=None):
        if not limiter_id:
            self.set_status(400)
            self.write_json({'reason': 'Invalid data', 'description': self._('Invalid data')})
            return

        access_token = self.request.headers.get('X-AUTH-HOLMES', None)

        if access_token is None:
            self.set_status(403)
            self.write_json({'reason': 'Empty access token', 'description': self._('Empty access token')})
            return

        result = yield User.authenticate(
            access_token,
            self.application.http_client.fetch,
            self.db,
            self.application.config
        )

        if result and result.get('user', None) is None:
            self.set_status(401)
            self.write_json({'reason': 'Unauthorized user', 'description': self._('Unauthorized user')})
            return

        limiter = Limiter.by_id(limiter_id, self.db)

        if not limiter or not limiter.id:
            self.set_status(404)
            self.write_json({'reason': 'Not Found', 'description': self._('Not Found')})
            return

        Limiter.delete(limiter.id, self.db)

        yield self.cache.remove_domain_limiters_key()

        self.set_status(204)
