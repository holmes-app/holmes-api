#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
import os

from preggy import expect
from octopus.model import Response
from tests.fixtures import DomainFactory, PageFactory, db
from tests.unit.base import ApiTestCase
from mock import Mock
import requests

from holmes.reviewer import Reviewer
from holmes.models.review import Review
from holmes.models.page import Page
from holmes.models.domain import Domain
from holmes.utils import _
from holmes.config import Config
from holmes.worker import HolmesWorker
from holmes.server import HolmesApiServer


class CanProcessWebsiteTest(ApiTestCase, HolmesWorker):
    def __init__(self, *args, **kw):
        self.options = Mock(concurrency=10, verbose=0, cache=False)
        ApiTestCase.__init__(self, *args, **kw)
        self.db = db
        self.initialize()

    def connect_sqlalchemy(self):
        if not getattr(self, 'db', None):
            super(CanProcessWebsiteTest, self).connect_sqlalchemy()

    def async_get(self, url, handler, method='GET', **kw):
        response = requests.get(url)
        resp = Response(
            url=url, status_code=response.status_code,
            headers=dict([(key, value) for key, value in response.headers.items()]),
            cookies=dict([(key, value) for key, value in response.cookies.items()]),
            text=response.text, effective_url=response.url,
            error=response.status_code > 399 and response.text or None,
            request_time=response.elapsed and response.elapsed.total_seconds() or 0
        )

        handler(url, resp)

    def get_server(self):
        cfg = Config(**self.get_config())
        debug = os.environ.get('DEBUG_TESTS', 'False').lower() == 'true'

        self.server = HolmesApiServer(config=cfg, debug=debug, db=self.db)
        return self.server

    @property
    def config(self):
        conf = dict(
            SQLALCHEMY_CONNECTION_STRING="mysql+mysqldb://root@localhost:3306/test_holmes",
            SQLALCHEMY_POOL_SIZE=1,
            SQLALCHEMY_POOL_MAX_OVERFLOW=0,
            SQLALCHEMY_AUTO_FLUSH=True,
            COMMIT_ON_REQUEST_END=False,
            REDISHOST='localhost',
            REDISPORT=57575,
            REDISPUBSUB=True,
            MATERIAL_GIRL_REDISHOST='localhost',
            MATERIAL_GIRL_REDISPORT=57575,
            SEARCH_PROVIDER="holmes.search_providers.noexternal.NoExternalSearchProvider",
            FACTERS = [
                'holmes.facters.title.TitleFacter',
                'holmes.facters.links.LinkFacter',
                #'holmes.facters.robots.RobotsFacter',
                #'holmes.facters.sitemap.SitemapFacter',
                #'holmes.facters.images.ImageFacter',
                #'holmes.facters.css.CSSFacter',
                'holmes.facters.meta_tags.MetaTagsFacter',
                #'holmes.facters.js.JSFacter',
                'holmes.facters.body.BodyFacter',
                'holmes.facters.head.HeadFacter',
                'holmes.facters.last_modified.LastModifiedFacter',
                'holmes.facters.google_analytics.GoogleAnalyticsFacter',
                'holmes.facters.heading_hierarchy.HeadingHierarchyFacter',
            ],
            VALIDATORS = [
                'holmes.validators.title.TitleValidator',
                #'holmes.validators.link_crawler.LinkCrawlerValidator',
                #'holmes.validators.robots.RobotsValidator',
                #'holmes.validators.sitemap.SitemapValidator',
                #'holmes.validators.domain_canonicalization.DomainCanonicalizationValidator',
                #'holmes.validators.img_requests.ImageRequestsValidator',
                #'holmes.validators.css_requests.CSSRequestsValidator',
                #'holmes.validators.js_requests.JSRequestsValidator',
                #'holmes.validators.image_alt.ImageAltValidator',
                'holmes.validators.anchor_without_any_text.AnchorWithoutAnyTextValidator',
                'holmes.validators.meta_tags.MetaTagsValidator',
                #'holmes.validators.meta_robots.MetaRobotsValidator',
                'holmes.validators.required_meta_tags.RequiredMetaTagsValidator',
                'holmes.validators.links_with_rel_nofollow.LinkWithRelNofollowValidator',
                #'holmes.validators.link_with_redirect.LinkWithRedirectValidator',
                'holmes.validators.schema_org_item_type.SchemaOrgItemTypeValidator',
                'holmes.validators.body.BodyValidator',
                'holmes.validators.link_with_rel_canonical.LinkWithRelCanonicalValidator',
                'holmes.validators.blacklist.BlackListValidator',
                'holmes.validators.open_graph.OpenGraphValidator',
                'holmes.validators.last_modified.LastModifiedValidator',
                'holmes.validators.google_analytics.GoogleAnalyticsValidator',
                'holmes.validators.heading_hierarchy.HeadingHierarchyValidator',
                'holmes.validators.url_with_underscore.UrlWithUnderscoreValidator',
            ]
        )
        conf['MAX_JS_REQUESTS_PER_PAGE'] = 0
        conf['MAX_JS_KB_PER_PAGE_AFTER_GZIP'] = 0
        conf['MAX_CSS_REQUESTS_PER_PAGE'] = 0
        conf['MAX_CSS_KB_PER_PAGE_AFTER_GZIP'] = 0

        return Config(**conf)

    def get_reviewer(
            self, api_url=None, page_uuid=None, page_url='http://page.url',
            page_score=0.0, config=None):

        if api_url is None:
            api_url = self.get_url('/')

        if page_uuid is None:
            page_uuid = str(uuid4())

        if config is None:
            config = self.config

        return Reviewer(
            api_url=api_url,
            page_uuid=str(page_uuid),
            page_url=page_url,
            page_score=0.0,
            config=config,
            validators=self.validators,
            facters=self.facters,
            search_provider=self.search_provider,
            wait=self.otto.wait,
            wait_timeout=0,  # max time to wait for all requests to finish
            db=self.db,
            cache=self.cache,
            publish=self.publish,
            async_get=self.async_get,
            fact_definitions=self.fact_definitions,
            violation_definitions=self.violation_definitions,
        )


    def test_can_process_globo_com(self):
        self.db.query(Review).delete()
        self.db.query(Page).delete()
        self.db.query(Domain).delete()

        domain = DomainFactory.create(name='globo.com', url='http://www.globo.com')

        page = PageFactory.create(domain=domain, url='http://www.globo.com/')

        reviewer = self.get_reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url='http://www.globo.com/'
        )

        reviewer.review()

        loaded_page = self.db.query(Page).get(page.id)
        review = loaded_page.last_review

        expect(len(review.facts)).to_be_greater_than(3)
        expect(len(review.violations)).to_be_greater_than(3)

        print
        print
        msg = 'Evaluation for "http://www.globo.com"'
        print msg
        print '=' * len(msg)

        print
        print 'Facts'
        print '-----'
        for fact in review.facts:
            print fact.to_dict(reviewer.fact_definitions, _)

        print
        print 'Violations'
        print '----------'
        for violation in review.violations:
            print violation.to_dict(reviewer.violation_definitions, _)

        print
        print
