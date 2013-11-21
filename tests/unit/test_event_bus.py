#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect
from mock import Mock

from holmes.event_bus import EventBus
from tests.unit.base import ApiTestCase


class TestEventBus(ApiTestCase):
    def get_bus(self):
        redis = Mock()
        app = Mock(
            redis=redis,
            redis_pub_sub=redis
        )
        return redis, app, EventBus(app)

    def test_create_event_bus(self):
        redis, app, bus = self.get_bus()

        expect(bus.application).to_equal(app)
        expect(bus.handlers).to_be_empty()
        expect(bus.publish_items).to_be_empty()

        redis.subscribe.assert_called_once_with('events', bus.on_message)

    def test_can_subscribe(self):
        redis, app, bus = self.get_bus()
        callback = Mock()

        bus.subscribe('channel', 'uuid', callback)
        expect(bus.handlers).to_include('channel')
        expect(bus.handlers['channel']).to_include('uuid')
        expect(bus.handlers['channel']['uuid']).to_equal(callback)

    def test_can_unsubscribe(self):
        redis, app, bus = self.get_bus()

        bus.subscribe('channel', 'uuid', Mock())
        bus.unsubscribe('channel', 'uuid')

        expect(bus.handlers).to_be_like({
            'channel': {}
        })

    def test_can_unsubscribe_if_invalid_channel(self):
        redis, app, bus = self.get_bus()

        bus.unsubscribe('channel', 'uuid')

        expect(bus.handlers).to_be_empty()

    def test_can_unsubscribe_if_invalid_uuid(self):
        redis, app, bus = self.get_bus()

        bus.subscribe('channel', 'uuid', Mock())
        bus.unsubscribe('channel', 'uuid')
        bus.unsubscribe('channel', 'uuid')

        expect(bus.handlers).to_be_like({
            'channel': {}
        })

    def test_can_publish(self):
        redis, app, bus = self.get_bus()

        bus.publish('message')

        expect(bus.publish_items).to_include(('events', 'message'))

    def test_can_flush(self):
        redis, app, bus = self.get_bus()

        bus.publish('message')
        bus.publish('message2')

        bus.flush()

        expect(bus.publish_items).to_be_empty()

        redis.publish.assert_any_call('events', 'message')
        redis.publish.assert_any_call('events', 'message2')

    def test_on_message_returns_if_null_message(self):
        redis, app, bus = self.get_bus()
        handler_mock = Mock()

        bus.handlers['events']['uuid'] = handler_mock

        expect(bus.on_message(None)).to_be_null()

        expect(handler_mock.called).to_be_false()

    def test_on_message_when_type_not_message(self):
        redis, app, bus = self.get_bus()
        handler_mock = Mock()

        bus.handlers['events']['uuid'] = handler_mock

        bus.on_message(('type', 'events', 'value'))

        expect(handler_mock.called).to_be_false()

    def test_on_message_when_type_message(self):
        redis, app, bus = self.get_bus()
        handler_mock = Mock()

        bus.handlers['events']['uuid'] = handler_mock

        bus.on_message(('message', 'events', 'value'))

        expect(handler_mock.called).to_be_true()
