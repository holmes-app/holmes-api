#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import factory
import factory.alchemy
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from holmes.models import (
    Domain, Page, Review, Violation, Fact, Key, KeysCategory, Request,
    User, Limiter, DomainsViolationsPrefs, UsersViolationsPrefs
)
from uuid import uuid4

autoflush = True
engine = create_engine(
    "mysql+mysqldb://root@localhost:3306/test_holmes",
    convert_unicode=True,
    pool_size=1,
    max_overflow=0,
    echo=False
)
maker = sessionmaker(bind=engine, autoflush=autoflush)
db = scoped_session(maker)


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = db

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        instance = super(BaseFactory, cls)._create(target_class, *args, **kwargs)
        if (hasattr(cls, '_meta')
           and cls._meta is not None
           and hasattr(cls._meta, 'sqlalchemy_session')
           and cls._meta.sqlalchemy_session is not None):
            cls._meta.sqlalchemy_session.flush()
        return instance


class DomainFactory(BaseFactory):
    class Meta:
        model = Domain

    name = factory.Sequence(lambda n: 'domain-{0}.com'.format(n))
    url = factory.Sequence(lambda n: 'http://my-site-{0}.com/'.format(n))
    is_active = True


class PageFactory(BaseFactory):
    class Meta:
        model = Page

    url = factory.Sequence(lambda n: 'http://my-site.com/{0}/'.format(n))
    url_hash = None
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

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs['url_hash'] = hashlib.sha512(kwargs['url']).hexdigest()
        return kwargs


class ReviewFactory(BaseFactory):
    class Meta:
        model = Review

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
                key = Key.get_or_create(db, 'key.%d' % i, 'category.%d' % (i % 3))
                violations.append(
                    Violation(
                        key=key,
                        value="value %d" % i,
                        points=i,
                        domain=kwargs['page'].domain,
                        review_is_active=kwargs['is_active']
                    )
                )

            kwargs['violations'] = violations

        if 'number_of_facts' in kwargs:
            number_of_facts = kwargs['number_of_facts']
            del kwargs['number_of_facts']

            facts = []
            for i in range(number_of_facts):
                key = Key.get_or_create(db, 'key.%d' % i, 'category.%d' % (i % 3))
                facts.append(Fact(key=key, value="value %d" % i))

            kwargs['facts'] = facts

        return kwargs


class KeysCategoryFactory(BaseFactory):
    class Meta:
        model = KeysCategory

    name = factory.Sequence(lambda n: 'category-{0}'.format(n))


class KeyFactory(BaseFactory):
    class Meta:
        model = Key

    name = factory.Sequence(lambda n: 'key-{0}'.format(n))
    category = factory.SubFactory(KeysCategoryFactory)


class FactFactory(BaseFactory):
    class Meta:
        model = Fact

    key = factory.SubFactory(KeyFactory)
    value = None


class ViolationFactory(BaseFactory):
    class Meta:
        model = Violation

    key = factory.SubFactory(KeyFactory)
    value = None
    points = 0
    domain = factory.SubFactory(DomainFactory)
    review_is_active = True


class RequestFactory(BaseFactory):
    class Meta:
        model = Request

    domain_name = 'g1.globo.com'
    url = 'http://g1.globo.com'
    effective_url = 'http://g1.globo.com/'
    status_code = 301
    response_time = 0.23
    completed_date = datetime.date(2013, 02, 12)
    review_url = 'http://globo.com/'


class UserFactory(BaseFactory):
    class Meta:
        model = User

    fullname = 'Marcelo Jorge Vieira'
    email = 'marcelo.vieira@corp.globo.com'
    is_superuser = True
    last_login = datetime.datetime(2013, 12, 11, 10, 9, 8)


class LimiterFactory(BaseFactory):
    class Meta:
        model = Limiter

    url = factory.Sequence(lambda n: 'http://my-site-{0}.com/'.format(n))
    url_hash = None
    value = 10

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs['url_hash'] = hashlib.sha512(kwargs['url']).hexdigest()
        return kwargs


class DomainsViolationsPrefsFactory(BaseFactory):
    class Meta:
        model = DomainsViolationsPrefs

    domain = factory.SubFactory(DomainFactory)
    key = factory.SubFactory(KeyFactory)
    value = 'whatever'


class UsersViolationsPrefsFactory(BaseFactory):
    class Meta:
        model = UsersViolationsPrefs

    user = factory.SubFactory(UserFactory)
    key = factory.SubFactory(KeyFactory)
    is_active = True
