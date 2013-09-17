#!/usr/bin/python
# -*- coding: utf-8 -*-

import factory

from holmes.models import Domain, Page, Processing
from tests.base import MotorEngineFactory


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
    last_processing = None


class ProcessingFactory(MotorEngineFactory):
    FACTORY_FOR = Processing

    created_date = None
    page = None
