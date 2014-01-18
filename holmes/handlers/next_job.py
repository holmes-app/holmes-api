#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import choice
from datetime import datetime, timedelta

from tornado import gen
from tornado.web import asynchronous

from holmes.handlers import BaseHandler
from holmes.models import Domain, Page, Settings


class NextJobHandler(BaseHandler):

    @gen.coroutine
    @asynchronous
    def get(self):
        expired_time = datetime.now() - timedelta(seconds=self.application.config.REVIEW_EXPIRATION_IN_SECONDS)

        settings = Settings.instance(self.db)

        active_domains = [item.id for item in self.db.query(Domain.id).filter(Domain.is_active).all()]

        pages_in_need_of_review = self.db.query(Page.uuid, Page.url, Page.score, Page.last_review_date) \
            .filter(Page.last_review_date == None) \
            .filter(Page.domain_id.in_(active_domains)) \
            .order_by(Page.score.desc())[:200]

        if len(pages_in_need_of_review) == 0:
            pages_in_need_of_review = self.db.query(Page.uuid, Page.url, Page.score, Page.last_review_date) \
                .filter(Page.last_review_date <= expired_time) \
                .order_by(Page.score.desc())[:200]

            if len(pages_in_need_of_review) == 0:
                if settings.lambda_score > 0:
                    self.update_pages_score_by(settings, settings.lambda_score, self.handle_scores_updated)
                    return

                self.write('')
                self.finish()
                return

        if settings.lambda_score > pages_in_need_of_review[0].score:
            self.update_pages_score_by(settings, settings.lambda_score, self.handle_scores_updated)
            return

        page = choice(pages_in_need_of_review)

        if page.last_review_date is not None and page.last_review_date > expired_time:
            self.write('')
            self.finish()
            return

        self.write_json({
            'page': str(page.uuid),
            'url': page.url,
            'score': page.score
        })
        self.finish()

    def handle_scores_updated(self, scores_updated):
        self.write('')
        self.finish()

    def update_pages_score_by(self, settings, score, callback):
        self.cache.has_lock('lambda-page', callback=self.handle_lambda_has_lock(settings, score, callback))

    def handle_lambda_has_lock(self, settings, score, callback):
        def handle(has_lock):
            if has_lock:
                callback(False)
                return

            settings.lambda_score = 0
            self.cache.lock_page('lambda-page', callback=self.handle_lambda_lock_acquired(score, callback))

        return handle

    def handle_lambda_lock_acquired(self, score, callback):
        def handle(*args, **kw):
            self.cache.get_page_count(callback=self.handle_got_page_count(score, callback))

        return handle

    def handle_got_page_count(self, score, callback):
        def handle(count):
            individual_score = float(score) / float(count)
            Page.update_scores(individual_score, self.db)
            self.cache.release_lock_page('lambda-page', callback=self.handle_lambda_page_released(callback))

        return handle

    def handle_lambda_page_released(self, callback):
        def handle(*args, **kw):
            callback(True)
        return handle
