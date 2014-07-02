#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from uuid import uuid4

import holmes.utils as utils
from tornado.websocket import WebSocketHandler


class EventBusHandler(WebSocketHandler):

    @property
    def config(self):
        return self.application.config

    def initialize(self, *args, **kw):
        super(EventBusHandler, self).initialize(*args, **kw)

        self.jwt = utils.Jwt(self.config.SECRET_KEY)

    def keep_alive(self):
        return True

    def is_authenticated(self):
        return self.jwt.try_to_decode(self.get_cookie('HOLMES_AUTH_TOKEN'))

    def open(self):
        if self.is_authenticated()[0]:
            self.uuid = uuid4()
            logging.debug("WebSocket opened.")
            self.application.event_bus.subscribe(
                'events', self.uuid, self.async_callback(self.on_event)
            )
        else:
            self.close()

    def on_event(self, message):
        if self.ws_connection is not None:
            self.write_message(message)

    def on_close(self):
        if hasattr(self, 'uuid'):
            self.application.event_bus.unsubscribe('events', self.uuid)
        logging.debug("WebSocket closed.")
