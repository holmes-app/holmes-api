#!/usr/bin/python
# -*- coding: utf-8 -*-

import factory

from holmes.models import Domain, Page, Review, Worker
from tests.base import MotorEngineFactory
from uuid import uuid4


class DomainFactory(MotorEngineFactory):
    FACTORY_FOR = Domain

    name = factory.Sequence(lambda n: 'domain-{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://my-site-{0}.com/'.format(n))


class PageFactory(MotorEngineFactory):
    FACTORY_FOR = Page

    title = factory.Sequence(lambda n: 'page-{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://my-site.com/{0}/'.format(n))

    added_date = None
    updated_date = None

    domain = None
    last_review = None


class ReviewFactory(MotorEngineFactory):
    FACTORY_FOR = Review

    facts = factory.LazyAttribute(lambda a: [])
    violations = factory.LazyAttribute(lambda a: [])

    created_date = None
    page = None


class WorkerFactory(MotorEngineFactory):
    FACTORY_FOR = Worker

    uuid = factory.LazyAttribute(lambda a: uuid4())
    last_ping = None
