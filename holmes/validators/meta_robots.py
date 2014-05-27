#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class MetaRobotsValidator(Validator):
    META_ROBOTS_NO_INDEX = _('A meta tag with the robots="noindex" '
                             'attribute tells the search engines that '
                             'they should not index this page.')

    META_ROBOTS_NO_FOLLOW = _('A meta tag with the robots="nofollow" '
                              'attribute tells the search engines that they '
                              'should not follow any links in this page.')

    @classmethod
    def get_violation_definitions(cls):
        return {
            'presence.meta.robots.noindex': {
                'title': _('Meta Robots with value of noindex'),
                'description': cls.META_ROBOTS_NO_INDEX,
                'category': _('SEO'),
                'generic_description': cls.META_ROBOTS_NO_INDEX
            },
            'presence.meta.robots.nofollow': {
                'title': _('Meta Robots with value of nofollow'),
                'description': cls.META_ROBOTS_NO_FOLLOW,
                'category': _('SEO'),
                'generic_description': cls.META_ROBOTS_NO_FOLLOW
            }
        }

    def validate(self):
        tags = self.get_meta_tags()

        for tag in tags:
            if tag['key'] == 'robots' and tag['content'] == 'noindex':
                self.add_violation(
                    key='presence.meta.robots.noindex',
                    value=None,
                    points=80
                )

            if tag['key'] == 'robots' and tag['content'] == 'nofollow':
                self.add_violation(
                    key='presence.meta.robots.nofollow',
                    value=None,
                    points=50
                )

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
