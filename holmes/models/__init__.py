#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from holmes.models.domain import Domain  # NOQA
from holmes.models.page import Page  # NOQA
from holmes.models.review import Review  # NOQA
from holmes.models.fact import Fact  # NOQA
from holmes.models.violation import Violation  # NOQA
from holmes.models.worker import Worker  # NOQA
