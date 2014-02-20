#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import dumps
from preggy import expect
from tornado.testing import gen_test
from tornado.gen import Task

from holmes.cache import Cache
from holmes.models import Domain, Delimiter, Page, Request
from tests.unit.base import ApiTestCase
from tests.fixtures import (
    DomainFactory, PageFactory, ReviewFactory, DelimiterFactory, RequestFactory
)


class CacheTestCase(ApiTestCase):
    @property
    def cache(self):
        return self.server.application.cache

    def test_cache_is_in_server(self):
        expect(self.server.application.cache).to_be_instance_of(Cache)

    def test_cache_has_connection_to_redis(self):
        expect(self.server.application.cache.redis).not_to_be_null()

    def test_cache_has_connection_to_db(self):
        expect(self.server.application.cache.db).not_to_be_null()

    @gen_test
    def test_can_get_page_count_per_domain(self):
        self.db.query(Domain).delete()

        globocom = DomainFactory.create(url="http://globo.com", name="globo.com")
        g1 = DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        for i in range(2):
            PageFactory.create(domain=globocom)
            PageFactory.create(domain=g1)

        PageFactory.create(domain=g1)

        page_count = yield self.cache.get_page_count('globo.com')
        expect(page_count).to_equal(2)

        page_count = yield self.cache.get_page_count('g1.globo.com')
        expect(page_count).to_equal(3)

        # should get from cache
        self.cache.db = None

        page_count = yield self.cache.get_page_count('g1.globo.com')
        expect(page_count).to_equal(3)

    @gen_test
    def test_increment_active_review_count(self):
        key = 'g.com-active-review-count'
        self.cache.redis.delete(key)

        gcom = DomainFactory.create(url='http://g.com', name='g.com')
        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=1
        )

        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=False,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=3
        )

        page_count = yield self.cache.get_active_review_count('g.com')
        expect(page_count).to_equal(1)

        yield self.cache.increment_active_review_count('g.com')
        page_count = yield self.cache.get_active_review_count('g.com')
        expect(page_count).to_equal(2)

    @gen_test
    def test_increment_violations_count(self):
        key = 'g.com-violation-count'
        self.cache.redis.delete(key)

        gcom = DomainFactory.create(url='http://g.com', name='g.com')
        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=10
        )

        violation_count = yield self.cache.get_violation_count(gcom.name)
        expect(violation_count).to_equal(10)

        yield self.cache.increment_violations_count(gcom.name)
        violation_count = yield self.cache.get_violation_count(gcom.name)
        expect(violation_count).to_equal(11)

    @gen_test
    def test_can_increment_page_count(self):
        self.db.query(Domain).delete()

        globocom = DomainFactory.create(url="http://globo.com", name="globo.com")

        for i in range(2):
            PageFactory.create(domain=globocom)

        page_count = yield self.cache.get_page_count('globo.com')
        expect(page_count).to_equal(2)

        page_count = yield self.cache.increment_page_count('globo.com', 10)
        expect(page_count).to_equal(12)

    @gen_test
    def test_can_increment_page_count_without_domain(self):
        self.db.query(Domain).delete()

        key = 'page-page-count'
        self.cache.redis.delete(key)

        globocom = DomainFactory.create(url="http://globo.com", name="globo.com")
        g1 = DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        for i in range(2):
            PageFactory.create(domain=globocom)

        for i in range(3):
            PageFactory.create(domain=g1)

        page_count = yield self.cache.get_page_count()
        expect(page_count).to_equal(5)

        page_count = yield self.cache.increment_page_count()
        expect(page_count).to_equal(6)

    @gen_test
    def test_can_get_violation_count_for_domain(self):
        self.db.query(Domain).delete()

        globocom = DomainFactory.create(url="http://globo.com", name="globo.com")

        page = PageFactory.create(domain=globocom)
        ReviewFactory.create(is_active=True, is_complete=True, domain=globocom, page=page, number_of_violations=10)

        violation_count = yield self.cache.get_violation_count('globo.com')
        expect(violation_count).to_equal(10)

        # should get from cache
        self.cache.db = None

        violation_count = yield self.cache.get_violation_count('globo.com')
        expect(violation_count).to_equal(10)

    @gen_test
    def test_can_get_active_review_count_for_domain(self):
        self.db.query(Domain).delete()

        globocom = DomainFactory.create(url="http://globo.com", name="globo.com")
        DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        page = PageFactory.create(domain=globocom)
        ReviewFactory.create(is_active=True, is_complete=True, domain=globocom, page=page, number_of_violations=10)
        page2 = PageFactory.create(domain=globocom)
        ReviewFactory.create(is_active=True, is_complete=True, domain=globocom, page=page2, number_of_violations=10)
        ReviewFactory.create(is_active=False, is_complete=True, domain=globocom, page=page2, number_of_violations=10)

        count = yield self.cache.get_active_review_count('globo.com')
        expect(count).to_equal(2)

        # should get from cache
        self.cache.db = None

        count = yield self.cache.get_active_review_count('globo.com')
        expect(count).to_equal(2)

    @gen_test
    def test_can_get_good_request_count_for_domain(self):
        self.db.query(Request).delete()
        self.db.query(Domain).delete()
        DomainFactory.create(url='http://globo.com', name='globo.com')

        key = 'globo.com-good-request-count'
        self.cache.redis.delete(key)

        RequestFactory.create(status_code=200, domain_name='globo.com')
        RequestFactory.create(status_code=304, domain_name='globo.com')
        RequestFactory.create(status_code=400, domain_name='globo.com')
        RequestFactory.create(status_code=403, domain_name='globo.com')
        RequestFactory.create(status_code=404, domain_name='globo.com')

        good = yield self.cache.get_good_request_count('globo.com')
        expect(good).to_equal(2)

        self.cache.db = None

        good = yield self.cache.get_good_request_count('globo.com')
        expect(good).to_equal(2)

    @gen_test
    def test_can_get_bad_request_count_for_domain(self):
        self.db.query(Request).delete()
        self.db.query(Domain).delete()
        DomainFactory.create(url='http://globo.com', name='globo.com')

        key = 'globo.com-bad-request-count'
        self.cache.redis.delete(key)

        RequestFactory.create(status_code=200, domain_name='globo.com')
        RequestFactory.create(status_code=304, domain_name='globo.com')
        RequestFactory.create(status_code=400, domain_name='globo.com')
        RequestFactory.create(status_code=403, domain_name='globo.com')
        RequestFactory.create(status_code=404, domain_name='globo.com')

        bad = yield self.cache.get_bad_request_count('globo.com')
        expect(bad).to_equal(3)

        self.cache.db = None

        bad = yield self.cache.get_bad_request_count('globo.com')
        expect(bad).to_equal(3)

    @gen_test
    def test_can_get_response_time_avg_for_domain(self):
        self.db.query(Request).delete()
        self.db.query(Domain).delete()
        DomainFactory.create(url='http://globo.com', name='globo.com')

        key = 'globo.com-response-time-avg'
        self.cache.redis.delete(key)

        RequestFactory.create(status_code=200, domain_name='globo.com', response_time=0.25)
        RequestFactory.create(status_code=304, domain_name='globo.com', response_time=0.35)
        RequestFactory.create(status_code=400, domain_name='globo.com', response_time=0.25)
        RequestFactory.create(status_code=403, domain_name='globo.com', response_time=0.35)
        RequestFactory.create(status_code=404, domain_name='globo.com', response_time=0.25)

        avg = yield self.cache.get_response_time_avg('globo.com')
        expect(avg).to_be_like(0.3)

        self.cache.db = None

        avg = yield self.cache.get_response_time_avg('globo.com')
        expect(avg).to_be_like(0.3)

    @gen_test
    def test_can_store_processed_page_lock(self):
        yield self.cache.lock_page('http://www.globo.com')

        result = yield Task(self.cache.redis.get, 'http://www.globo.com-lock')
        expect(int(result)).to_equal(1)

    @gen_test
    def test_can_get_url_was_added(self):
        yield self.cache.lock_page('http://www.globo.com')

        result = yield self.cache.has_lock('http://www.globo.com')
        expect(result).to_be_true()

    @gen_test
    def test_release_lock_page(self):
        yield self.cache.lock_page('http://www.globo.com')

        result = yield self.cache.has_lock('http://www.globo.com')
        expect(result).to_be_true()

        yield self.cache.release_lock_page('http://www.globo.com')

        result = yield self.cache.has_lock('http://www.globo.com')
        expect(result).to_be_false()

class SyncCacheTestCase(ApiTestCase):
    def setUp(self):
        super(SyncCacheTestCase, self).setUp()
        self.db.query(Domain).delete()
        self.db.query(Page).delete()

    @property
    def sync_cache(self):
        return self.connect_to_sync_redis()

    @property
    def config(self):
        return self.server.application.config

    def test_cache_has_connection_to_redis(self):
        expect(self.sync_cache.redis).not_to_be_null()

    def test_cache_has_connection_to_db(self):
        expect(self.sync_cache.db).not_to_be_null()

    def test_can_get_domain_limiters(self):
        self.db.query(Delimiter).delete()
        self.sync_cache.redis.delete('domain-limiters')

        domains = self.sync_cache.get_domain_limiters()
        expect(domains).to_be_null()

        delimiter = DelimiterFactory.create(url='http://test.com/')
        DelimiterFactory.create()
        DelimiterFactory.create()

        domains = self.sync_cache.get_domain_limiters()

        expect(domains).to_length(3)
        expect(domains).to_include({delimiter.url: delimiter.value})

        # should get from cache
        self.sync_cache.db = None

        domains = self.sync_cache.get_domain_limiters()
        expect(domains).to_length(3)

    def test_can_set_domain_limiters(self):
        self.db.query(Delimiter).delete()
        self.sync_cache.redis.delete('domain-limiters')

        domains = self.sync_cache.get_domain_limiters()
        expect(domains).to_be_null()

        delimiters = [{u'http://test.com/': 10}]

        self.sync_cache.set_domain_limiters(delimiters, 120)
        domains = self.sync_cache.get_domain_limiters()

        expect(domains).to_length(1)
        expect(domains).to_include(delimiters[0])

    def test_has_key(self):
        self.sync_cache.redis.delete('my-key')
        has_my_key = self.sync_cache.has_key('my-key')
        expect(has_my_key).to_be_false()

        self.sync_cache.redis.setex('my-key', 10, '')
        has_my_key = self.sync_cache.has_key('my-key')
        expect(has_my_key).to_be_true()

    def test_get_domain_name(self):
        testcom = self.sync_cache.get_domain_name('test.com')
        expect(testcom).to_equal('test.com')

        gcom = DomainFactory.create(url='http://g.com', name='g.com')
        domain_name = self.sync_cache.get_domain_name(gcom)
        expect(domain_name).to_equal('g.com')

        empty_domain_name = self.sync_cache.get_domain_name('')
        expect(empty_domain_name).to_equal('page')

    def test_increment_violations_count(self):
        key = 'g.com-violation-count'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url='http://g.com', name='g.com')
        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=10
        )

        self.sync_cache.increment_violations_count(gcom.name)
        violation_count = self.sync_cache.redis.get(key)
        expect(violation_count).to_equal('10')

        self.sync_cache.increment_violations_count(gcom.name)
        violation_count = self.sync_cache.redis.get(key)
        expect(violation_count).to_equal('11')

    def test_increment_active_review_count(self):
        key = 'g.com-active-review-count'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url='http://g.com', name='g.com')
        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=1
        )

        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=False,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=3
        )

        self.sync_cache.increment_active_review_count(gcom.name)
        active_review_count = self.sync_cache.redis.get(key)
        expect(active_review_count).to_equal('1')

        self.sync_cache.increment_active_review_count(gcom.name)
        active_review_count = self.sync_cache.redis.get(key)
        expect(active_review_count).to_equal('2')

    def test_increment_page_count(self):
        key = 'g.com-page-count'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        PageFactory.create(domain=gcom)

        self.sync_cache.increment_page_count(gcom.name)
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('1')

        self.sync_cache.increment_page_count(gcom.name)
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('2')

    def test_increment_page_count_without_domain(self):
        key = 'page-page-count'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        g1 = DomainFactory.create(url="http://g1.com", name="g1.com")

        for i in range(2):
            PageFactory.create(domain=gcom)

        PageFactory.create(domain=g1)

        self.sync_cache.increment_page_count()
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('3')

        self.sync_cache.increment_page_count()
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('4')

    def test_increment_count(self):
        key = 'g.com-my-key'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        PageFactory.create(domain=gcom)

        self.sync_cache.increment_count(
            'my-key',
            gcom.name,
            lambda domain: domain.get_page_count(self.db)
        )
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('1')

        self.sync_cache.increment_count(
            'my-key',
            gcom.name,
            lambda domain: domain.get_page_count(self.db)
        )
        page_count = self.sync_cache.redis.get(key)
        expect(page_count).to_equal('2')

    def test_get_page_count(self):
        self.sync_cache.redis.delete('g.com-page-count')

        gcom = DomainFactory.create(url="http://g.com", name="g.com")

        for i in range(2):
            PageFactory.create(domain=gcom)

        page_count = self.sync_cache.get_page_count(gcom.name)
        expect(page_count).to_equal(2)

        # should get from cache
        self.sync_cache.db = None

        page_count = self.sync_cache.get_page_count(gcom.name)
        expect(page_count).to_equal(2)

    def test_get_page_count_without_domain(self):
        self.sync_cache.redis.delete('page-page-count')

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        g1 = DomainFactory.create(url="http://g1.com", name="g1.com")

        for i in range(2):
            PageFactory.create(domain=gcom)

        for i in range(3):
            PageFactory.create(domain=g1)


        page_count = self.sync_cache.get_page_count()
        expect(page_count).to_equal(5)

        # should get from cache
        self.sync_cache.db = None

        page_count = self.sync_cache.get_page_count()
        expect(page_count).to_equal(5)

    def test_get_violation_count(self):
        self.sync_cache.redis.delete('g.com-violation-count')

        gcom = DomainFactory.create(url="http://g.com", name="g.com")

        page = PageFactory.create(domain=gcom)
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=10
        )

        violation_count = self.sync_cache.get_violation_count(gcom.name)
        expect(violation_count).to_equal(10)

        # should get from cache
        self.sync_cache.db = None

        violation_count = self.sync_cache.get_violation_count(gcom.name)
        expect(violation_count).to_equal(10)


    def test_get_active_review_count(self):
        self.sync_cache.redis.delete('g.com-active-review-count')

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        page = PageFactory.create(domain=gcom)
        page2 = PageFactory.create(domain=gcom)

        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page,
            number_of_violations=10
        )
        ReviewFactory.create(
            is_active=True,
            is_complete=True,
            domain=gcom,
            page=page2,
            number_of_violations=10
        )
        ReviewFactory.create(
            is_active=False,
            is_complete=True,
            domain=gcom,
            page=page2,
            number_of_violations=10
        )

        count = self.sync_cache.get_active_review_count(gcom.name)
        expect(count).to_equal(2)

        # should get from cache
        self.sync_cache.db = None

        count = self.sync_cache.get_active_review_count(gcom.name)
        expect(count).to_equal(2)

    def test_get_count(self):
        key = 'g.com-my-key'
        self.sync_cache.redis.delete(key)

        gcom = DomainFactory.create(url="http://g.com", name="g.com")
        PageFactory.create(domain=gcom)

        count = self.sync_cache.get_count(
            key,
            gcom.name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_page_count(self.db)
        )
        expect(count).to_equal(1)

        # should get from cache
        self.sync_cache.db = None

        count = self.sync_cache.get_count(
            key,
            gcom.name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_page_count(self.db)
        )
        expect(count).to_equal(1)

    def test_get_request_with_url_not_cached(self):
        url = 'http://g.com/test.html'
        key = 'urls-%s' % url

        self.sync_cache.redis.delete(key)

        url, response = self.sync_cache.get_request(url)

        expect(url).to_equal('http://g.com/test.html')
        expect(response).to_be_null()

    def test_get_request_with_url_cached(self):
        url = 'http://g.com/test.html'
        key = 'urls-%s' % url

        self.sync_cache.redis.delete(key)

        self.sync_cache.redis.setex(
            key,
            10,
            dumps({
                'url': url,
                'status_code': 200,
                'headers': None,
                'cookies': None,
                'effective_url': 'http://g.com/test.html',
                'error': None,
                'request_time': str(100)
            })
        )

        url, response = self.sync_cache.get_request(url)

        expect(url).to_equal('http://g.com/test.html')
        expect(response.status_code).to_equal(200)
        expect(response.effective_url).to_equal(url)
        expect(response.request_time).to_equal(100)

    def test_set_request(self):
        test_url = 'http://g.com/test.html'
        key = 'urls-%s' % test_url

        self.sync_cache.redis.delete(key)

        url, response = self.sync_cache.get_request(test_url)
        expect(url).to_equal('http://g.com/test.html')
        expect(response).to_be_null()

        self.sync_cache.set_request(
            url=url,
            status_code=200,
            headers={'X-HEADER': 'test'},
            cookies=None,
            text=None,
            effective_url='http://g.com/test.html',
            error=None,
            request_time=100,
            expiration=5
        )

        url, response = self.sync_cache.get_request(test_url)

        expect(url).to_equal('http://g.com/test.html')
        expect(response.status_code).to_equal(200)
        expect(response.headers.get('X-HEADER')).to_equal('test')
        expect(response.cookies).to_be_null()
        expect(response.effective_url).to_equal(url)
        expect(response.error).to_be_null()
        expect(response.request_time).to_equal(100)

    def test_set_request_with_status_code_greater_than_399(self):
        test_url = 'http://g.com/test.html'
        key = 'urls-%s' % test_url

        self.sync_cache.redis.delete(key)

        self.sync_cache.set_request(
            url=test_url,
            status_code=500,
            headers=None,
            cookies=None,
            text=None,
            effective_url=None,
            error=None,
            request_time=1,
            expiration=5
        )

        url, response = self.sync_cache.get_request(test_url)
        expect(url).to_equal('http://g.com/test.html')
        expect(response).to_be_null()

    def test_set_request_with_status_code_less_than_100(self):
        test_url = 'http://g.com/test.html'
        key = 'urls-%s' % test_url

        self.sync_cache.redis.delete(key)

        self.sync_cache.set_request(
            url=test_url,
            status_code=99,
            headers=None,
            cookies=None,
            text=None,
            effective_url=None,
            error=None,
            request_time=1,
            expiration=5
        )

        url, response = self.sync_cache.get_request(test_url)
        expect(url).to_equal('http://g.com/test.html')
        expect(response).to_be_null()

    def test_lock_next_job(self):
        test_url = 'http://g.com/test.html'
        key = '%s-next-job-lock' % test_url

        self.sync_cache.redis.delete(key)

        lock = self.sync_cache.lock_next_job(test_url, 5)

        expect(lock.acquire()).to_be_true()

    def test_has_next_job_lock(self):
        test_url = 'http://g.com/test.html'
        key = '%s-next-job-lock' % test_url

        self.sync_cache.redis.delete(key)

        lock = self.sync_cache.lock_next_job(test_url, 20)
        expect(lock).not_to_be_null()

        has_next_job_lock = self.sync_cache.has_next_job_lock(test_url, 20)
        expect(has_next_job_lock).not_to_be_null()

        has_next_job_lock = self.sync_cache.has_next_job_lock(test_url, 20)
        expect(has_next_job_lock).to_be_null()

    def test_release_next_job(self):
        test_url = 'http://g.com/test.html'
        key = '%s-next-job-lock' % test_url

        self.sync_cache.redis.delete(key)

        has_next_job_lock = self.sync_cache.has_next_job_lock(test_url, 5)
        expect(has_next_job_lock).not_to_be_null()

        self.sync_cache.release_next_job(has_next_job_lock)

        lock = self.sync_cache.has_next_job_lock(test_url, 5)
        expect(lock).not_to_be_null()
