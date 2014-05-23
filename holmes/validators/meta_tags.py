#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class MetaTagsValidator(Validator):

    @classmethod
    def get_violation_definitions(cls):
        return {
            'absent.metatags': {
                'title': _('Meta tags not present'),
                'description': _(
                    'No meta tags found on this page. This is damaging for '
                    'Search Engines.'
                ),
                'category': _('HTTP'),
                'generic_description': _(
                    'Validates the presence of metatags. They are important '
                    'to inform metadata about the HTML document. '
                    'The absent of metatags are damaging for search '
                    'engines. Meta elements are typically used to specify '
                    'page description, keywords, author of the document, last '
                    'modified, and other metadata.'
                )
            },
            'page.metatags.description_too_big': {
                'title': _('Maximum size of description meta tag'),
                'description': _(
                    'The meta description tag is longer than %(max_size)s '
                    'characters. It is best to keep meta descriptions '
                    'shorter for better indexing on search engines.'
                ),
                'category': _('SEO'),
                'generic_description': _(
                    'Validates the size of a description metatag. It is best '
                    'to keep meta descriptions shorter for better indexing on '
                    'search engines. This limit is configurable by Holmes '
                    'Configuration.'
                ),
                'unit': 'number'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'page.metatags.description_too_big': {
                'value': config.METATAG_DESCRIPTION_MAX_SIZE,
                'description': config.get_description('METATAG_DESCRIPTION_MAX_SIZE')
            }
        }

    def validate(self):
        max_size = self.get_violation_pref('page.metatags.description_too_big')

        meta_tags = self.review.data.get('meta.tags', None)

        if not meta_tags:
            self.add_violation(
                key='absent.metatags',
                value='No metatags.',
                points=100
            )

        for mt in meta_tags:
            if mt['key'] == 'description' and len(mt['content']) > max_size:
                self.add_violation(
                    key='page.metatags.description_too_big',
                    value={'max_size': max_size},
                    points=20
                )
                break
