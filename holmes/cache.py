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
from retools.lock import Lock, LockTimeout

from holmes.models import Domain, Page, Limiter, Violation


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
    def increment_active_review_count(self, domain_name, increment=1, callback=None):
        self.increment_count(
            'active-review-count',
            domain_name,
            lambda domain: domain.get_active_review_count(self.db),
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

            if has_key:
                self.redis.incrby(key, increment, callback=callback)
            else:
                if domain is None:
                    value = Page.get_page_count(self.db) + increment - 1
                else:
                    value = get_default_method(domain) + increment - 1

                self.redis.set(key, value, callback=callback)

        return handle

    def data_handle_has_key(self, key, get_default_method, increment, callback):
        def handle(has_key):
            if has_key:
                self.redis.incrby(key, increment, callback=callback)
            else:
                value = get_default_method() + increment
                self.redis.set(key, value, callback=callback)

        return handle

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
    def get_top_in_category_for_domain(self, domain, key_category_id, limit, callback=None):
        self.get_data(
            '%s-top-violations-cat-%s' % (domain.name, key_category_id),
            int(self.config.TOP_CATEGORY_VIOLATIONS_EXPIRATION_IN_SECONDS),
            lambda: Violation.get_top_in_category_for_domain(self.db, domain, key_category_id, limit),
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

    def increment_active_review_count(self, domain_name, increment=1):
        self.increment_count(
            'active-review-count',
            domain_name,
            lambda domain: domain.get_active_review_count(self.db),
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

    def get_limiter_buckets(self, active_domains, avg_links_per_page=10.0):
        available = []
        all_limiters = reversed(sorted(Limiter.get_limiters_for_domains(self.db, active_domains), key=lambda item: item.url))

        for limiter in all_limiters:
            capacity = float(limiter.value - self.get_limit_usage(limiter.url))
            available.append((limiter, capacity))

        return available

    def fill_job_bucket(self, expiration, look_ahead_pages=1000, avg_links_per_page=10.0):
        try:
            with Lock('next-job-fill-bucket-lock', redis=self.redis):
                logging.info('Refilling job bucket. Lock acquired...')
                expired_time = datetime.utcnow() - timedelta(seconds=expiration)

                active_domains = Domain.get_active_domains(self.db)

                if not active_domains:
                    return

                active_domains_ids = [item.id for item in active_domains]

                limiter_buckets = self.get_limiter_buckets(active_domains, avg_links_per_page)

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

                logging.debug('Total of %d pages found to add to redis.' % (sum([len(item) for item in all_domains_pages_in_need_of_review])))

                item_count = int(self.redis.scard('next-job-bucket'))
                current_domain = 0
                while item_count < look_ahead_pages and len(all_domains_pages_in_need_of_review) > 0:
                    if current_domain >= len(all_domains_pages_in_need_of_review):
                        current_domain = 0

                    item = all_domains_pages_in_need_of_review[current_domain].pop(0)

                    has_limit = True
                    logging.debug('Available Limit Buckets: %s' % limiter_buckets)
                    for index, (limit, available) in enumerate(limiter_buckets):
                        if limit.matches(item.url):
                            if available <= 0:
                                has_limit = False
                                break
                            limiter_buckets[index] = (limit, available - 1)

                    if has_limit:
                        self.redis.sadd('next-job-bucket', dumps({
                            'page': str(item.uuid),
                            'url': item.url
                        }))

                        item_count += 1

                    # if there are not any more pages in this domain remove it from dictionary
                    if not all_domains_pages_in_need_of_review[current_domain]:
                        del all_domains_pages_in_need_of_review[current_domain]

                    current_domain += 1

                logging.debug('ADDED A TOTAL of %d ITEMS TO REDIS...' % item_count)

        except LockTimeout:
            logging.info("Can't acquire lock. Moving on...")

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
