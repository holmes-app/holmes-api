#!/usr/bin/python
# -*- coding: utf-8 -*-

from gzip import GzipFile
from cStringIO import StringIO
from datetime import datetime, timedelta
import logging

import msgpack
from tornado.concurrent import return_future
from ujson import loads, dumps
from octopus.model import Response
from sqlalchemy import or_
from retools.lock import Lock

from holmes.models import Domain, Page, Limiter, Violation, Request


class Cache(object):
    def __init__(self, application):
        self.application = application
        self.redis = self.application.redis
        self.db = self.application.db
        self.config = self.application.config

    def get_domain_name(self, domain_name):
        if isinstance(domain_name, Domain):
            return domain_name.name

        return domain_name or 'page'

    @return_future
    def has_key(self, key, callback):
        self.redis.exists(key, callback)

    @return_future
    def increment_violations_count(self, domain_name, increment=1, callback=None):
        self.increment_count(
            'violation-count',
            domain_name,
            lambda domain: domain.get_violation_data(self.db),
            increment,
            callback
        )

    @return_future
    def increment_active_review_count(self, domain_name, increment=1, callback=None):
        self.increment_count(
            'active-review-count',
            domain_name,
            lambda domain: domain.get_active_review_count(self.db),
            increment,
            callback
        )

    @return_future
    def increment_page_count(self, domain_name=None, increment=1, callback=None):
        self.increment_count(
            'page-count',
            domain_name,
            lambda domain: domain.get_page_count(self.db),
            increment,
            callback
        )

    def increment_count(self, key, domain_name, get_default_method, increment=1, callback=None):
        key = '%s-%s' % (self.get_domain_name(domain_name), key)
        self.has_key(key, self.handle_has_key(key, domain_name, get_default_method, increment, callback))

    def handle_has_key(self, key, domain_name, get_default_method, increment, callback):
        def handle(has_key):
            domain = domain_name
            if domain and not isinstance(domain, Domain):
                domain = Domain.get_domain_by_name(domain_name, self.db)

            #if not domain:
                #callback(None)
                #return

            if has_key:
                self.redis.incrby(key, increment, callback=callback)
            else:
                if domain is None:
                    value = Page.get_page_count(self.db) + increment - 1
                else:
                    value = get_default_method(domain) + increment - 1

                self.redis.set(key, value, callback=callback)

        return handle

    @return_future
    def increment_next_jobs_count(self, increment=1, callback=None):
        self.increment_data(
            'next-jobs',
            lambda: Page.get_next_jobs_count(self.db, self.config),
            increment,
            callback
        )

    @return_future
    def increment_requests_count(self, increment=1, callback=None):
        self.increment_data(
            'requests-count',
            lambda: Request.get_requests_count(self.db),
            increment,
            callback
        )

    def increment_data(self, key, get_default_method, increment=1, callback=None):
        self.has_key(key, self.data_handle_has_key(key, get_default_method, increment, callback))

    def data_handle_has_key(self, key, get_default_method, increment, callback):
        def handle(has_key):
            if has_key:
                self.redis.incrby(key, increment, callback=callback)
            else:
                value = get_default_method() + increment
                self.redis.set(key, value, callback=callback)

        return handle

    @return_future
    def get_page_count(self, domain_name=None, callback=None):
        self.get_count(
            'page-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_page_count(self.db),
            callback=callback
        )

    @return_future
    def get_violation_count(self, domain_name, callback=None):
        self.get_count(
            'violation-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_violation_data(self.db),
            callback=callback
        )

    @return_future
    def get_active_review_count(self, domain_name, callback=None):
        self.get_count(
            'active-review-count',
            domain_name,
            int(self.config.ACTIVE_REVIEW_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_active_review_count(self.db),
            callback=callback
        )

    @return_future
    def get_good_request_count(self, domain_name, callback=None):
        self.get_count(
            'good-request-count',
            domain_name,
            int(self.config.GOOD_REQUEST_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_good_request_count(self.db),
            callback=callback
        )

    @return_future
    def get_bad_request_count(self, domain_name, callback=None):
        self.get_count(
            'bad-request-count',
            domain_name,
            int(self.config.BAD_REQUEST_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_bad_request_count(self.db),
            callback=callback
        )

    @return_future
    def get_response_time_avg(self, domain_name, callback=None):
        self.get_avg(
            'response-time-avg',
            domain_name,
            int(self.config.RESPONSE_TIME_AVG_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_response_time_avg(self.db),
            callback=callback
        )

    @return_future
    def get_top_in_category_for_domain(self, domain, key_category_id, limit, callback=None):
        self.get_data(
            '%s-top-violations-cat-%s' % (domain.name, key_category_id),
            int(self.config.TOP_CATEGORY_VIOLATIONS_EXPIRATION_IN_SECONDS),
            lambda: Violation.get_top_in_category_for_domain(self.db, domain, key_category_id, limit),
            callback=callback
        )

    @return_future
    def get_most_common_violations(self, violation_definitions, sample_limit, callback=None):
        self.get_data(
            'most-common-violations',
            int(self.config.MOST_COMMON_VIOLATIONS_CACHE_EXPIRATION),
            lambda: Violation.get_most_common_violations(self.db, violation_definitions, sample_limit),
            callback=callback
        )

    @return_future
    def get_next_jobs_count(self, callback=None):
        self.get_data(
            'next-jobs',
            int(self.config.NEXT_JOBS_COUNT_EXPIRATION_IN_SECONDS),
            lambda: Page.get_next_jobs_count(self.db, self.config),
            callback=callback
        )

    @return_future
    def get_requests_count(self, callback=None):
        self.get_data(
            'requests-count',
            int(self.config.REQUESTS_COUNT_EXPIRATION_IN_SECONDS),
            lambda: Request.get_requests_count(self.db),
            callback=callback
        )

    def get_domain(self, domain_name):
        domain = domain_name
        if domain and not isinstance(domain, Domain):
            domain = Domain.get_domain_by_name(domain_name, self.db)
        return domain

    def get_count(self, key, domain_name, expiration, get_count_method, callback=None):
        cache_key = '%s-%s' % (self.get_domain_name(domain_name), key)
        self.redis.get(cache_key, callback=self.handle_get_count(key, domain_name, expiration, get_count_method, callback))

    def handle_get_count(self, key, domain_name, expiration, get_count_method, callback):
        def handle(count):
            if count is not None:
                callback(int(count))
                return

            domain = self.get_domain(domain_name)

            if domain is None:
                count = Page.get_page_count(self.db)
            else:
                count = get_count_method(domain)

            cache_key = '%s-%s' % (self.get_domain_name(domain), key)

            self.redis.setex(
                key=cache_key,
                value=int(count),
                seconds=expiration,
                callback=self.handle_set_count(count, callback)
            )

        return handle

    def handle_set_count(self, count, callback):
        def handle(*args, **kw):
            callback(count)

        return handle

    def get_avg(self, key, domain_name, expiration, get_avg_method, callback=None):
        cache_key = '%s-%s' % (self.get_domain_name(domain_name), key)
        self.redis.get(cache_key, callback=self.handle_get_avg(key, domain_name, expiration, get_avg_method, callback))

    def handle_get_avg(self, key, domain_name, expiration, get_avg_method, callback):
        def handle(avg):
            if avg is not None:
                callback(float(avg))
                return

            domain = self.get_domain(domain_name)

            avg = get_avg_method(domain)

            cache_key = '%s-%s' % (self.get_domain_name(domain), key)

            self.redis.setex(
                key=cache_key,
                value=float(avg),
                seconds=expiration,
                callback=self.handle_set_avg(avg, callback)
            )

        return handle

    def handle_set_avg(self, avg, callback):
        def handle(*args, **kw):
            callback(avg)

        return handle

    def get_data(self, key, expiration, get_data_method, callback=None):
        self.redis.get(key, callback=self.handle_get_data(key, expiration, get_data_method, callback))

    def handle_get_data(self, key, expiration, get_data_method, callback):
        def handle(data):
            if data is not None:
                callback(loads(data))
                return

            data = get_data_method()

            self.redis.setex(
                key=key,
                value=dumps(data),
                seconds=expiration,
                callback=self.handle_set_data(data, callback)
            )

        return handle

    def handle_set_data(self, data, callback):
        def handle(*args, **kw):
            callback(data)

        return handle

    @return_future
    def lock_page(self, url, callback=None):
        expiration = self.config.URL_LOCK_EXPIRATION_IN_SECONDS

        self.redis.setex(
            key='%s-lock' % url,
            value=1,
            seconds=expiration,
            callback=callback
        )

    @return_future
    def has_lock(self, url, callback=None):
        self.redis.get(
            key='%s-lock' % url,
            callback=self.handle_get_lock_page(url, callback)
        )

    def handle_get_lock_page(self, url, callback):
        def handle(value):
            callback(value == '1')

        return handle

    @return_future
    def release_lock_page(self, url, callback):
        self.redis.delete('%s-lock' % url, callback=callback)

    @return_future
    def get_limit_usage(self, url, callback):
        self.redis.zcard('limit-for-%s' % url, callback=callback)

    @return_future
    def get_limit_usage_by_domain(self, domain_url, callback):
        self.redis.keys('limit-for-%s*' % domain_url, callback)

    @return_future
    def delete_limit_usage_by_domain(self, domain_url, callback):
        self.get_limit_usage_by_domain(
            domain_url,
            callback=self.handle_delete_limit_usage_by_domain(domain_url, callback)
        )

    def handle_delete_limit_usage_by_domain(self, domain_url, callback):
        def handle(keys):
            self.redis.delete(keys)
            callback()
        return handle

    @return_future
    def remove_domain_limiters_key(self, callback):
        self.redis.delete('domain-limiters', callback=callback)

    @return_future
    def increment_page_score(self, page_id, increment=1, callback=None):
        self.redis.zincrby('page-scores', increment, page_id, callback=callback)


class SyncCache(object):
    def __init__(self, db, redis, config):
        self.db = db
        self.redis = redis
        self.config = config

    def has_key(self, key):
        return self.redis.exists(key)

    def get_domain_name(self, domain_name):
        if isinstance(domain_name, Domain):
            return domain_name.name

        return domain_name or 'page'

    def increment_violations_count(self, domain_name, increment=1):
        self.increment_count(
            'violation-count',
            domain_name,
            lambda domain: domain.get_violation_data(self.db),
            increment
        )

    def increment_active_review_count(self, domain_name, increment=1):
        self.increment_count(
            'active-review-count',
            domain_name,
            lambda domain: domain.get_active_review_count(self.db),
            increment,
        )

    def increment_page_count(self, domain_name=None, increment=1):
        self.increment_count(
            'page-count',
            domain_name,
            lambda domain: domain.get_page_count(self.db),
            increment,
        )

    def increment_count(self, key, domain_name, get_default_method, increment=1):
        key = '%s-%s' % (self.get_domain_name(domain_name), key)

        has_key = self.has_key(key)

        domain = domain_name
        if domain and not isinstance(domain, Domain):
            domain = Domain.get_domain_by_name(domain_name, self.db)

        if has_key:
            self.redis.incrby(key, increment)
        else:
            if domain is None:
                value = Page.get_page_count(self.db) + increment - 1
            else:
                value = get_default_method(domain) + increment - 1

            self.redis.set(key, value)

    def increment_next_jobs_count(self, increment=1):
        self.increment_data(
            'next-jobs',
            lambda: Page.get_next_jobs_count(self.db, self.config),
            increment
        )

    def increment_requests_count(self, increment=1):
        self.increment_data(
            'requests-count',
            lambda: Request.get_requests_count(self.db),
            increment
        )

    def increment_data(self, key, get_default_method, increment=1):
        has_key = self.has_key(key)

        if has_key:
            self.redis.incrby(key, increment)
        else:
            value = get_default_method() + increment
            self.redis.set(key, value)

    def get_page_count(self, domain_name=None):
        return self.get_count(
            'page-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_page_count(self.db),
        )

    def get_violation_count(self, domain_name):
        return self.get_count(
            'violation-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_violation_data(self.db),
        )

    def get_active_review_count(self, domain_name):
        return self.get_count(
            'active-review-count',
            domain_name,
            int(self.config.ACTIVE_REVIEW_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_active_review_count(self.db)
        )

    def get_count(self, key, domain_name, expiration, get_count_method):
        cache_key = '%s-%s' % (self.get_domain_name(domain_name), key)

        count = self.redis.get(cache_key)

        if count is not None:
            return int(count)

        domain = domain_name
        if domain and not isinstance(domain, Domain):
            domain = Domain.get_domain_by_name(domain_name, self.db)

        if domain is None:
            count = Page.get_page_count(self.db)
        else:
            count = get_count_method(domain)

        cache_key = '%s-%s' % (self.get_domain_name(domain), key)

        self.redis.setex(
            cache_key,
            expiration,
            value=int(count)
        )

        return int(count)

    def get_request(self, url):
        cache_key = "urls-%s" % url

        contents = self.redis.get(cache_key)

        if not contents:
            return url, None

        item = msgpack.unpackb(contents)

        text = GzipFile(mode='r', fileobj=StringIO(item['body'])).read()

        response = Response(
            url=url,
            status_code=item['status_code'],
            headers=item['headers'],
            cookies=item['cookies'],
            text=text,
            effective_url=item['effective_url'],
            error=item['error'],
            request_time=float(item['request_time'])
        )

        response.from_cache = True

        return url, response

    def set_request(self, url, status_code, headers, cookies, text, effective_url, error, request_time, expiration):
        if status_code > 399 or status_code < 100:
            return

        cache_key = "urls-%s" % url

        out = StringIO()
        with GzipFile(fileobj=out, mode="w") as f:
            f.write(text)
        text = out.getvalue()

        value = msgpack.packb({
            'url': url,
            'body': text,
            'status_code': status_code,
            'headers': headers,
            'cookies': cookies,
            'effective_url': effective_url,
            'error': error,
            'request_time': request_time
        })

        self.redis.setex(
            cache_key,
            expiration,
            value,
        )

    def lock_next_job(self, url, expiration):
        return self.redis.lock('%s-next-job-lock' % url, expiration)

    def has_next_job_lock(self, url, expiration):
        lock = self.lock_next_job(url, expiration)
        has_acquired = lock.acquire(blocking=False)
        if not has_acquired:
            return None
        return lock

    def release_next_job(self, lock):
        return lock.release()

    def set_domain_limiters(self, domains, expiration):
        self.redis.setex(
            'domain-limiters',
            expiration,
            dumps(domains)
        )

    def get_domain_limiters(self):
        domains = self.redis.get('domain-limiters')

        if domains:
            domains = loads(domains)
        else:
            limiters = Limiter.get_all(self.db)
            if limiters:
                domains = [{d.url: d.value} for d in limiters]
                self.set_domain_limiters(
                    domains,
                    self.config.LIMITER_VALUES_CACHE_EXPIRATION
                )

        return domains

    def get_limit_usage(self, url):
        return self.redis.zcard('limit-for-%s' % url)

    def increment_page_score(self, page_id, increment=1):
        self.redis.zincrby('page-scores', page_id, increment)

    def seized_pages_score(self):
        pages = self.redis.zrange('page-scores', 0, -1, withscores=True)
        self.redis.zremrangebyrank('page-scores', 0, -1)
        return pages

    def lock_update_pages_score(self, expiration):
        return self.redis.lock('update-pages-score-lock', expiration)

    def has_update_pages_lock(self, expiration):
        lock = self.lock_update_pages_score(expiration)
        has_acquired = lock.acquire(blocking=False)
        if not has_acquired:
            return None
        return lock

    def release_update_pages_lock(self, lock):
        return lock.release()

    def fill_job_bucket(self, expiration, look_ahead_pages=1000):
        with Lock('next-job-fill-bucket-lock', redis=self.redis):
            expired_time = datetime.utcnow() - timedelta(seconds=expiration)

            active_domains = Domain.get_active_domains(self.db)
            active_domains_ids = [item.id for item in active_domains]

            all_domains_pages_in_need_of_review = []

            for domain_id in active_domains_ids:
                pages = self.db \
                    .query(
                        Page.uuid,
                        Page.url,
                        Page.score,
                        Page.last_review_date
                    ) \
                    .filter(Page.domain_id == domain_id) \
                    .filter(or_(
                        Page.last_review_date == None,
                        Page.last_review_date <= expired_time
                    )) \
                    .order_by(Page.last_review_date.asc())[:look_ahead_pages]

                if pages:
                    all_domains_pages_in_need_of_review.append(pages)

            item_count = int(self.redis.scard('next-job-bucket'))
            current_domain = 0
            while item_count < look_ahead_pages and len(all_domains_pages_in_need_of_review) > 0:
                if current_domain >= len(all_domains_pages_in_need_of_review):
                    current_domain = 0

                item = all_domains_pages_in_need_of_review[current_domain].pop(0)

                # if there are not any more pages in this domain remove it from dictionary
                if not all_domains_pages_in_need_of_review[current_domain]:
                    del all_domains_pages_in_need_of_review[current_domain]

                self.redis.sadd('next-job-bucket', dumps({
                    'page': str(item.uuid),
                    'url': item.url
                }))

                current_domain += 1
                item_count += 1

    def get_next_job(self, expiration, look_ahead_pages=1000):
        logging.info('Getting next job from the bucket...')
        item = self.redis.spop('next-job-bucket')

        job_bucket_count = self.redis.scard('next-job-bucket')
        if job_bucket_count < look_ahead_pages * 0.1:
            logging.info('Bucket near empty (%d items). Must refill...' % job_bucket_count)
            self.fill_job_bucket(expiration, look_ahead_pages)

        if item is None:
            return None

        item = loads(item)
        logging.debug('Next job found: %s' % item['url'])

        return item
