#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect

from holmes.models import Settings
from tests.unit.base import ApiTestCase


class TestSettings(ApiTestCase):

    def test_can_get_instance(self):
        settings = Settings.instance(self.db)

        expect(settings.lambda_score).to_equal(0)
