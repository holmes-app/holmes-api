#!/usr/bin/python
# -*- coding: utf-8 -*-

import factory
import factory.alchemy

from holmes.models import Domain, Page, Review, Worker, Violation, Fact, Key
from uuid import uuid4


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        instance = super(BaseFactory, cls)._create(target_class, *args, **kwargs)
        if hasattr(cls, 'FACTORY_SESSION') and cls.FACTORY_SESSION is not None:
            cls.FACTORY_SESSION.flush()
        return instance


class DomainFactory(BaseFactory):
    FACTORY_FOR = Domain

    name = factory.Sequence(lambda n: 'domain-{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://my-site-{0}.com/'.format(n))
    is_active = True


class PageFactory(BaseFactory):
    FACTORY_FOR = Page

    url = factory.Sequence(lambda n: 'http://my-site.com/{0}/'.format(n))
    uuid = factory.LazyAttribute(lambda a: uuid4())

    created_date = None
    last_review_date = None

    last_modified = None
    expires = None

    domain = factory.SubFactory(DomainFactory)
    last_review = None

    violations_count = 0

    last_review_uuid = None

    score = 0.0


class ReviewFactory(BaseFactory):
    FACTORY_FOR = Review

    facts = factory.LazyAttribute(lambda a: [])
    violations = factory.LazyAttribute(lambda a: [])

    is_complete = False
    is_active = False
    created_date = None
    completed_date = None
    uuid = factory.LazyAttribute(lambda a: uuid4())

    domain = factory.SubFactory(DomainFactory)
    page = factory.SubFactory(PageFactory)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        if 'page' in kwargs:
            kwargs['domain'] = kwargs['page'].domain

        if 'page' in kwargs and 'uuid' in kwargs:
            kwargs['page'].last_review_uuid = kwargs['uuid']

        if 'number_of_violations' in kwargs:
            number_of_violations = kwargs['number_of_violations']
            del kwargs['number_of_violations']

            if 'page' in kwargs:
                kwargs['page'].violations_count = number_of_violations

            violations = []
            for i in range(number_of_violations):
                db = cls.FACTORY_SESSION
                key = Key.get_or_create(db, "violation.%d" % i)
                violations.append(
                    Violation(key=key, value="value %d" % i, points=i)
                )

            kwargs['violations'] = violations

        return kwargs


class KeyFactory(BaseFactory):
    FACTORY_FOR = Key

    name = factory.Sequence(lambda n: 'key-{0}'.format(n))


class FactFactory(BaseFactory):
    FACTORY_FOR = Fact

    key = factory.SubFactory(KeyFactory)
    value = None


class ViolationFactory(BaseFactory):
    FACTORY_FOR = Violation

    key = factory.SubFactory(KeyFactory)
    value = None
    points = 0


class WorkerFactory(BaseFactory):
    FACTORY_FOR = Worker

    uuid = factory.LazyAttribute(lambda a: uuid4())
    last_ping = None
    current_url = None
