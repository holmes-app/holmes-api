#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from time import time
from ujson import loads


class NoOpEventBus(object):
    def __init__(self, application):
        self.application = application

    def subscribe(self, channel, uuid, handler):
        pass

    def unsubscribe(self, channel, uuid):
        pass

    def publish(self, message):
        pass

    def flush(self):
        pass


class EventBus(object):
    def __init__(self, application):
        self.application = application
        self.handlers = defaultdict(dict)

        self.last_message = {}
        self.throttling = self.application.config.EVENT_BUS_THROTTLING_MESSAGE_TYPE

        self.publish_items = []
        self.application.redis_pub_sub.subscribe('events', self.on_message)

    def subscribe(self, channel, uuid, handler):
        self.handlers[channel][uuid] = handler

    def unsubscribe(self, channel, uuid):
        if self.handlers.get(channel, {}).get(uuid, None) is None:
            return

        del self.handlers[channel][uuid]

    def publish(self, message):
        self.publish_items.append(('events', message))

    def flush(self):
        for channel, message in self.publish_items:
            logging.debug('Publishing message to %s...' % channel)
            self.application.redis.publish(channel, message)
        self.publish_items = []

    def get_time(self):
        return time()

    def on_message(self, message):
        if message is None:
            return

        msg_type, msg_channel, msg_value = message

        if msg_type != 'message':
            return

        msg_obj = loads(msg_value)

        tp = msg_obj['type']

        if tp in self.throttling and tp in self.last_message and self.get_time() - self.last_message[tp] <= self.throttling[tp]:
            return

        logging.debug("%s on %s for %s" % (msg_type, msg_channel, msg_value))
        self.last_message[tp] = self.get_time()

        for handler in self.handlers.get(msg_channel, {}).values():
            handler(msg_value)
