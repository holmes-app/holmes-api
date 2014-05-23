#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class ImageAltValidator(Validator):
    @classmethod
    def get_without_alt_parsed_value(cls, value):
        result = []
        for src, name in value:
            data = '<a href="%s" target="_blank">%s</a>' % (src, name)
            result.append(data)

        return {'images': ', '.join(result)}

    @classmethod
    def get_alt_too_big_parsed_value(cls, value):
        result = []
        for src, name, alt in value['images']:
            data = u'<a href="{}" alt="{}" target="_blank">{}</a>'.format(
                src, alt, name
            )
            result.append(data)

        return {
            'max_size': value['max_size'],
            'images': ', '.join(result)
        }

    @classmethod
    def get_violation_definitions(cls):
        return {
            'invalid.images.alt': {
                'title': _('Image(s) without alt attribute'),
                'description': _(
                    'Images without alt text are not good for '
                    'Search Engines. Images without alt were '
                    'found for: %(images)s.'),
                'value_parser': cls.get_without_alt_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Images without alt attribute are not good for '
                    'search engines. They are searchable by the content '
                    'of this attribute, so if it\'s empty, it cause bad '
                    'indexing optimization.'
                )
            },
            'invalid.images.alt_too_big': {
                'title': _('Image(s) with alt attribute too big'),
                'description': _(
                    'Images with alt text bigger than %(max_size)d chars are '
                    'not good for search engines. Images with a too big alt '
                    'were found for: %(images)s.'),
                'value_parser': cls.get_alt_too_big_parsed_value,
                'category': _('SEO'),
                'generic_description': _(
                    'Images with alt text too long are not good to SEO. '
                    'This maximum value are configurable '
                    'by Holmes configuration.'
                ),
                'unit': 'number'
            }
        }

    @classmethod
    def get_default_violations_values(cls, config):
        return {
            'invalid.images.alt_too_big': {
                'value': config.MAX_IMAGE_ALT_SIZE,
                'description': config.get_description('MAX_IMAGE_ALT_SIZE')
            }
        }

    def validate(self):
        max_alt_size = self.get_violation_pref('invalid.images.alt_too_big')

        imgs = self.get_imgs()

        result_no_alt = []
        result_alt_too_big = []
        for img in imgs:
            src = img.get('src')
            if not src:
                continue

            src = self.normalize_url(src)
            img_alt = img.get('alt')

            if src:
                name = src.rsplit('/', 1)[-1]
                if not img_alt:
                    result_no_alt.append((src, name))
                elif len(img_alt) > max_alt_size:
                    result_alt_too_big.append((src, name, img_alt))

        if result_no_alt:
            self.add_violation(
                key='invalid.images.alt',
                value=result_no_alt,
                points=20 * len(result_no_alt)
            )

        if result_alt_too_big:
            self.add_violation(
                key='invalid.images.alt_too_big',
                value={
                    'images': result_alt_too_big,
                    'max_size': max_alt_size
                },
                points=20 * len(result_alt_too_big)
            )

    def get_imgs(self):
        return self.review.data.get('page.all_images', None)
