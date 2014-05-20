#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class ImageRequestsValidator(Validator):

    @classmethod
    def get_broken_images_message(cls, value):
        return 'The image(s) in "%s" could not be found or took ' \
               'more than 10 seconds to load.' % (
                   ', '.join(
                   [
                       '<a href="%s" target="_blank">Link #%s</a>' % (url,
                                                                      index)
                       for index, url in enumerate(value)
                   ]))

    @classmethod
    def get_requests_images_message(cls, value):
        return 'This page has %d image requests (%d over limit). ' \
               'Having too many requests impose a tax in the browser ' \
               'due to handshakes.' % (value['total'], value['limit'])

    @classmethod
    def get_total_size_message(cls, value):
        return 'There`s %.2fkb of images in this page and that ' \
               'adds up to more download time slowing down the page ' \
               'rendering to the user.' % value

    @classmethod
    def get_single_image_size_message(cls, value):
        if 'over_max_size' in value:
            data = []
            for url, size_img in value['over_max_size']:
                size = size_img - value['limit']
                name = url.rsplit('/', 1)[-1]
                if size > 0:
                    desc = ' (%dkb above limit)' % (size)
                else:
                    desc = ''
                data.append(
                    '<a href="%s" target="_blank">%s</a>%s' % (url, name, desc)
                )

            return 'Some images are above the expected limit (%dkb): %s' % (
                value['limit'], ', '.join(data))

    @classmethod
    def get_violation_definitions(cls):
        return {
            'broken.img': {
                'title': 'Image not found',
                'description': cls.get_broken_images_message,
                'category': 'HTTP',
                'generic_description': (
                    'Image tags without a valid image resource. '
                    'The pointed resource can be a Client or a '
                    'Server Error, they can be loaded too slow or, '
                    'in most cases, means a not founded image.'
                )
            },
            'single.size.img': {
                'title': 'Single image size in kb is too big',
                'description': cls.get_single_image_size_message,
                'category': 'Performance',
                'generic_description': (
                    'Images with a too big size is very bad to site '
                    'performance. This limits are configurable in '
                    'Holmes configuration.'
                )
            },
            'total.requests.img': {
                'title': 'Too many image requests',
                'description': cls.get_requests_images_message,
                'category': 'Performance',
                'generic_description': (
                    'A site with too many images requests per page can '
                    'deacrease the page load speed and performance. This '
                    'limits are configurable in Holmes configuration.'
                )
            },
            'total.size.img': {
                'title': 'Total image size in kb is too big',
                'description': cls.get_total_size_message,
                'category': 'Performance',
                'generic_description': (
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
