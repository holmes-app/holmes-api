#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import time


class RedisLock(object):
    def __init__(self, redis, lock_key='redis-lock', lock_timeout=10):
        self.redis = redis
        self.lock_key = lock_key
        self.lock_timeout = lock_timeout
        self.callback = None
        self.release_callback = None

    def exec_callback(self, *args, **kw):
        if self.callback is not None:
            self.callback(*args, **kw)

    def acquire(self, callback):
        self.callback = callback
        self.now = int(time.time())
        self.redis.setnx(self.lock_key, self.now + self.lock_timeout + 1, self.handle_setnx)

    def handle_setnx(self, result):
        if result == 1 or result is True:
            self.acquire_time = self.now
            logging.debug('Lock key %s acquired (with setnx).' % self.lock_key)
            self.exec_callback(True)
            return

        self.redis.get(self.lock_key, self.handle_get_current_lock)

    def handle_get_current_lock(self, current_lock_timestamp):
        if not current_lock_timestamp:
            logging.debug('Lock key %s could not be acquired (by getting current lock).' % self.lock_key)
            self.exec_callback(False)
            return

        self.current_lock_timestamp = int(current_lock_timestamp)

        if self.now > self.current_lock_timestamp:
            self.redis.getset(self.lock_key, self.now + self.lock_timeout + 1, self.handle_next_lock_timestamp)
        else:
            logging.debug('Lock key %s could not be acquired (because lock timestamp is greater than now).' % self.lock_key)
            self.exec_callback(False)

    def handle_next_lock_timestamp(self, next_lock_timestamp):
        if not next_lock_timestamp:
            logging.debug('Lock key %s could not be acquired (due to next lock timestamp).' % self.lock_key)
            self.exec_callback(False)
            return

        next_lock_timestamp = int(next_lock_timestamp)

        if next_lock_timestamp == self.current_lock_timestamp:
            self.acquire_time = self.now
            logging.debug('Lock key %s acquired.' % self.lock_key)
            self.exec_callback(True)
            return

        logging.debug('Lock key %s could not be acquired (invalid timestamp).' % self.lock_key)
        self.exec_callback(False)

    def release(self, callback):
        self.release_callback = callback
        self.redis.delete(self.lock_key, callback=self.handle_lock_key_deleted)

    def handle_lock_key_deleted(self, deleted_count):
        logging.debug('Lock key %s deleted.' % self.lock_key)
        self.release_callback(deleted_count)
