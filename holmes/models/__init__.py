#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base
from ujson import dumps, loads
Base = declarative_base()


class JsonType(types.TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage::

        JSONEncodedDict(255)

    """

    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        value = dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value:
            value = loads(value)
        else:
            value = None
        return value


from holmes.models.domain import Domain  # NOQA
from holmes.models.page import Page  # NOQA
from holmes.models.review import Review  # NOQA
from holmes.models.fact import Fact  # NOQA
from holmes.models.violation import Violation  # NOQA
from holmes.models.worker import Worker  # NOQA
from holmes.models.keys import Key  # NOQA
from holmes.models.settings import Settings  # NOQA
from holmes.models.keys_category import KeysCategory  # NOQA
