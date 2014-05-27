#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator
from holmes.utils import _


class ImageRequestsValidator(Validator):

    @classmethod
    def get_broken_images_parsed_values(cls, value):
        return {'images': ', '.join([
            '<a href="%s" target="_blank">Link #%s</a>' % (url, index)
            for index, url in enumerate(value)
        ])}

    @classmethod
    def get_single_image_size_parsed_value(cls, value):
        if 'over_max_size' in value:
            data = []
            for url, size_img in value['over_max_size']:
                name = url.rsplit('/', 1)[-1]
                desc = ' (%dkb)' % (size_img)
                data.append(
                    '<a href="%s" target="_blank">%s</a>%s' % (url, name, desc)
                )

            return {
                'limit': value['limit'], 'images': ', '.join(data)
            }

    @classmethod
    def get_violation_definitions(cls):
        return {
            'broken.img': {
                'title': _('Image not found'),
                'description': _(
                    'The image(s) in "%(images)s" could not be found or '
                    'took more than 10 seconds to load.'),
                'value_parser': cls.get_broken_images_parsed_values,
                'category': _('HTTP'),
                'generic_description': _(
                    'Image tags without a valid image resource. '
                    'The pointed resource can be a Client or a '
                    'Server Error, they can be loaded too slow or, '
                    'in most cases, means a not founded image.'
                )
            },
            'single.size.img': {
                'title': _('Single image size in kb is too big'),
                'description': _(
                    'Some images are above the expected limit '
                    '(%(limit)dkb): %(images)s'
                ),
                'value_parser': cls.get_single_image_size_parsed_value,
                'category': _('Performance'),
                'generic_description': _(
                    'Images with a too big size is very bad to site '
                    'performance. This limits are configurable in '
                    'Holmes configuration.'
                )
            },
            'total.requests.img': {
                'title': _('Too many image requests'),
                'description': _(
                    'This page has %(total)d image requests (%(limit)d over '
                    'limit). Having too many requests impose a tax in the '
                    'browser due to handshakes.'),
                'category': _('Performance'),
                'generic_description': _(
                    'A site with too many images requests per page can '
                    'deacrease the page load speed and performance. This '
                    'limits are configurable in Holmes configuration.'
                )
            },
            'total.size.img': {
                'title': _('Total image size in kb is too big'),
                'description': _(
                    'There`s %.2fkb of images in this page and that '
                    'adds up to more download time slowing down the page '
                    'rendering to the user.'),
                'category': _('Performance'),
                'generic_description': _(
                    'A site with a too big total image size per page can '
                    'decrease the page load speed and performance. This '
                    'limits are configurable in Holmes configuration.'
                )
            }
        }

    def validate(self):
        img_files = self.get_images()
        total_size = self.get_images_size()

        broken_imgs = set()

        over_max_size = set()

        for url, response in img_files:

            if response.status_code > 399:
                broken_imgs.add(url)

            if response.text is not None:
                size_img = len(response.text) / 1024.0

                if size_img > self.reviewer.config.MAX_KB_SINGLE_IMAGE:
                    over_max_size.add((url, size_img))

        if broken_imgs:
            self.add_violation(
                key='broken.img',
                value=broken_imgs,
                points=50
            )

        if over_max_size:
            points = 0
            for url, size_img in over_max_size:
                size = size_img - self.reviewer.config.MAX_KB_SINGLE_IMAGE
                points += size

            self.add_violation(
                key='single.size.img',
                value={
                    'limit': self.reviewer.config.MAX_KB_SINGLE_IMAGE,
                    'over_max_size': over_max_size
                },
                points=points
            )

        if len(img_files) > self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.img',
                value={
                    'total': len(img_files),
                    'limit': len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE
                },
                points=5 * (len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE)
            )

        if total_size > self.reviewer.config.MAX_IMG_KB_PER_PAGE:
            self.add_violation(
                key='total.size.img',
                value=total_size,
                points=int(total_size - self.reviewer.config.MAX_IMG_KB_PER_PAGE)
            )

    def get_images(self):
        return self.review.data.get('page.images', None)

    def get_images_size(self):
        return self.review.data.get('total.size.img', 0)
