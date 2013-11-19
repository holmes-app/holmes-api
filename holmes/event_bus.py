#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from collections import defaultdict


class EventBus(object):
    def __init__(self, application):
        self.application = application
        self.handlers = defaultdict(dict)

        self.publish_items = []
        self.application.redis_pub_sub.subscribe('events', self.on_message)

    def subscribe(self, channel, uuid, handler):
        self.handlers[channel][uuid] = handler

    def unsubscribe(self, channel, uuid):
        if channel not in self.handlers or uuid not in self.handlers[channel]:
            return

        del self.handlers[channel][uuid]

    def publish(self, message):
        self.publish_items.append(('events', message))

    def flush(self):
        for channel, message in self.publish_items:
            logging.debug('Publishing message to %s...' % channel)
            self.application.redis.publish(channel, message)
        self.publish_items = []

    def on_message(self, message):
        msg_type, msg_channel, msg_value = message

        logging.debug("%s on %s for %s" % (msg_type, msg_channel, msg_value))

        if msg_type != 'message':
            return

        for handler in self.handlers.get(msg_channel, {}).values():
            handler(msg_value)
