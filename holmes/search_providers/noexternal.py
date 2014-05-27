#!/usr/bin/env python
# -*- coding: utf-8 -*-

from holmes.search_providers import SearchProvider
from holmes.models.review import Review

from tornado.concurrent import return_future


class NoExternalSearchProvider(SearchProvider):
    def __init__(self, config, db, io_loop=None):
        self.db = db

    def index_review(self, review):
        pass

    @return_future
    def get_by_violation_key_name(self, key_id, current_page=1, page_size=10, domain=None, page_filter=None, callback=None):
        reviews = Review.get_by_violation_key_name(
            db=self.db,
            key_id=key_id,
            current_page=current_page,
            page_size=page_size,
            domain_filter=domain.name if domain else None,
            page_filter=page_filter,
        )

        reviews_data = []
        for item in reviews:
            reviews_data.append({
                'uuid': item.review_uuid,
                'page': {
                    'uuid': item.page_uuid,
                    'url': item.url,
                    'completedAt': item.completed_date
                },
                'domain': item.domain_name,
            })

        callback({
            'reviews': reviews_data
        })

    @return_future
    def get_domain_active_reviews(self, domain, current_page=1, page_size=10, page_filter=None, callback=None):
        reviews = domain.get_active_reviews(
            db=self.db,
            page_filter=page_filter,
            current_page=current_page,
            page_size=page_size,
        )

        pages = []

        for page in reviews:
            pages.append({
                'url': page.url,
                'uuid': str(page.uuid),
                'violationCount': page.violations_count,
                'completedAt': page.last_review_date,
                'reviewId': str(page.last_review_uuid)
            })

        callback({'pages': pages})

    @classmethod
    def main(cls):
        pass

if __name__ == '__main__':
    NoExternalSearchProvider.main()
