#!/usr/bin/python
# -*- coding: utf-8 -*-

import factory
from tornado.concurrent import return_future

from holmes.models import Domain, Page, Review, Worker
from uuid import uuid4


class MotorEngineFactory(factory.base.Factory):
    """Factory for motorengine objects."""
    ABSTRACT_FACTORY = True

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        return target_class(*args, **kwargs)

    @classmethod
    @return_future
    def _create(cls, target_class, *args, **kwargs):
        callback = kwargs.get('callback', None)
        del kwargs['callback']
        instance = target_class(*args, **kwargs)
        instance.save(callback=callback)


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

    is_complete = False
    is_active = False
    created_date = None
    completed_date = None
    page = None


class WorkerFactory(MotorEngineFactory):
    FACTORY_FOR = Worker

    uuid = factory.LazyAttribute(lambda a: uuid4())
    last_ping = None
    current_review = None
