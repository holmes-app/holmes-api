#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class ImageRequestsValidator(Validator):

    def validate(self):
        img_files = self.get_images()
        total_size = self.get_images_size()

        for url, response in img_files:

            if response.status_code > 399:
                self.add_violation(
                    key='broken.img',
                    title='Image not found.',
                    description='The image in "%s" could not be found or took '
                                'more than 10 seconds to load.' % url,
                    points=50
                )

            if response.text is not None:
                size_img = len(response.text) / 1024.0

                if size_img > self.reviewer.config.MAX_KB_SINGLE_IMAGE:
                    self.add_violation(
                        key='single.size.img',
                        title='Single image size in kb is too big.',
                        description='Found a image bigger then limit %d (%d over limit): %s' % (
                            self.reviewer.config.MAX_KB_SINGLE_IMAGE,
                            size_img - self.reviewer.config.MAX_KB_SINGLE_IMAGE,
                            url
                        ),
                        points=size_img - self.reviewer.config.MAX_KB_SINGLE_IMAGE
                    )

        if len(img_files) > self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.img',
                title='Too many image requests.',
                description='This page has %d image requests (%d over limit). '
                            'Having too many requests impose a tax in the browser due to handshakes.' %
                    (len(img_files), len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE),
                points=5 * (len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE)
            )

        if total_size > self.reviewer.config.MAX_IMG_KB_PER_PAGE:
            self.add_violation(
                key='total.size.img',
                title='Total image size in kb is too big.',
                description='There`s %.2fkb of images in this page and that adds up to more download time slowing down '
                            'the page rendering to the user.' % total_size,
                points=int(total_size - self.reviewer.config.MAX_IMG_KB_PER_PAGE)
            )

    def get_images(self):
        return self.review.data.get('page.images', None)

    def get_images_size(self):
        return self.review.data.get('total.size.img', 0)
