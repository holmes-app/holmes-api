#!/usr/bin/python
# -*- coding: utf-8 -*-

import factory
from tornado.concurrent import return_future

from holmes.models import Domain, Page, Review, Worker, Violation
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

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if 'page' in kwargs and kwargs['page'] is not None:
            kwargs['domain'] = kwargs['page'].domain

        if 'number_of_violations' in kwargs:
            number_of_violations = kwargs['number_of_violations']
            del kwargs['number_of_violations']

            violations = []
            for i in range(number_of_violations):
                violations.append(Violation(
                    key="violation.%d" % i,
                    title="title %d" % i,
                    description="description %d" % i,
                    points=i
                ))

            kwargs['violations'] = violations

        return kwargs


class WorkerFactory(MotorEngineFactory):
    FACTORY_FOR = Worker

    uuid = factory.LazyAttribute(lambda a: uuid4())
    last_ping = None
    current_review = None
