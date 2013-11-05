#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator  # NOQA

BASE_VALIDATORS = [
    'holmes.validators.title.TitleValidator',
    'holmes.validators.img_requests.ImageRequestsValidator',
    'holmes.validators.total_requests.TotalRequestsValidator',
    'holmes.validators.css_requests.CSSRequestsValidator',
    'holmes.validators.js_requests.JSRequestsValidator',
    'holmes.validators.link_crawler.LinkCrawlerValidator',
    'holmes.validators.meta_tags.MetaTagsValidator',
]
