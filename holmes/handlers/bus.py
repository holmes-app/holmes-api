#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from uuid import uuid4

from tornado.websocket import WebSocketHandler


class EventBusHandler(WebSocketHandler):
    def keep_alive(self):
        return True

    def open(self):
        self.uuid = uuid4()
        logging.debug("WebSocket opened.")
        self.application.event_bus.subscribe('events', self.uuid, self.async_callback(self.on_event))

    def on_event(self, message):
        if self.ws_connection is not None:
            self.write_message(message)

    def on_close(self):
        if hasattr(self, 'uuid'):
            self.application.event_bus.unsubscribe('events', self.uuid)
        logging.debug("WebSocket closed.")
