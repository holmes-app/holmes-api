#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class MetaRobotsValidator(Validator):

    def validate(self):
        tags = self.get_meta_tags()

        for tag in tags:
            if tag['key'] == 'robots' and tag['content'] == 'noindex':
                self.add_violation(
                    key='presence.meta.robots.noindex',
                    title='Meta Robots with value of noindex',
                    description='A meta tag with the robots="noindex" '
                                'attribute tells the search engines that '
                                'they should not index this page.',
                    points=80
                )

            if tag['key'] == 'robots' and tag['content'] == 'nofollow':
                self.add_violation(
                    key='presence.meta.robots.nofollow',
                    title='Meta Robots with value of nofollow',
                    description='A meta tag with the robots="nofollow" '
                                'attribute tells the search engines that they '
                                'should not follow any links in this page.',
                    points=50
                )

    def get_meta_tags(self):
        return self.review.data.get('meta.tags', None)
