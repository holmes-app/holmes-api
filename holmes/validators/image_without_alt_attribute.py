#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class ImageWithoutAltAttributeValidator(Validator):
    @classmethod
    def get_empy_anchors_message(cls, value):
        result = []
        for src, name in value:
            data = '<a href="%s" target="_blank">%s</a>' % (src, name)
            result.append(data)

        return 'Images without alt text are not good for ' \
               'Search Engines. Images without alt were ' \
               'found for: %s.' % (', '.join(result))

    @classmethod
    def get_violation_definitions(cls):
        return {
            'invalid.images.alt': {
                'title': 'Image(s) without alt attribute',
                'description': cls.get_empy_anchors_message,
                'category': 'SEO'
            }
        }

    def validate(self):
        imgs = self.get_imgs()

        result = []
        for img in imgs:
            src = img.get('src')
            if not src:
                continue

            src = self.normalize_url(src)
            if src and not img.get('alt'):
                name = src.rsplit('/', 1)[-1]
                result.append((src, name))

        if result:
            self.add_violation(
                key='invalid.images.alt',
                value=result,
                points=20 * len(result)
            )

    def get_imgs(self):
        return self.review.data.get('page.all_images', None)
