#!/usr/bin/python
# -*- coding: utf-8 -*-


from cow.plugins.motorengine_plugin import MotorEnginePlugin
from preggy import expect
from mock import patch

import holmes.server
from tests.unit.base import ApiTestCase


class ApiServerTestCase(ApiTestCase):
    def test_healthcheck(self):
        response = self.fetch('/healthcheck')
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('WORKING')

    def test_server_handlers(self):
        srv = holmes.server.HolmesApiServer()
        handlers = srv.get_handlers()
        expect(handlers).not_to_be_null()
        expect(handlers).to_length(18)

    def test_server_plugins(self):
        srv = holmes.server.HolmesApiServer()
        plugins = srv.get_plugins()
        expect(plugins).to_length(1)
        expect(plugins[0]).to_equal(MotorEnginePlugin)

    @patch('holmes.server.HolmesApiServer')
    def test_server_main_function(self, server_mock):
        holmes.server.main()
        expect(server_mock.run.called).to_be_true()
