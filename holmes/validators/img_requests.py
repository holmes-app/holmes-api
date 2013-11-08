#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.validators.base import Validator


class ImageRequestsValidator(Validator):
    def validate(self):
        img_files = self.get_img_requests()

        self.add_fact(
            key='total.requests.img',
            value=len(img_files),
            title='Total images requests'
        )

        results = self.process_img_requests(img_files)

        total_size = 0
        for item in results.values():
            size_img = len(item['content']) / 1024.0
            total_size += size_img

            if size_img > self.reviewer.config.MAX_KB_SINGLE_IMAGE:
                self.add_violation(
                    key='single.size.img',
                    title='Single image size in kb is too big.',
                    description='Found a image bigger then limit %d (%d over limit): %s' % (
                        self.reviewer.config.MAX_KB_SINGLE_IMAGE,
                        size_img - self.reviewer.config.MAX_KB_SINGLE_IMAGE,
                        item['url']
                    ),
                    points=size_img - self.reviewer.config.MAX_KB_SINGLE_IMAGE
                )

        self.add_fact(
            key='total.size.img',
            value=total_size,
            unit='kb',
            title='Total images size'
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

    def get_img_requests(self):
        return self.reviewer.current['html'].cssselect('img[src]')

    def process_img_requests(self, img_files):
        results = {}
        for img_file in img_files:
            src = img_file.get('src')
            if not src:
                continue

            is_absolute = self.is_absolute(src)

            if not is_absolute:
                src = self.rebase(src)

            response = self.get_response(src)

            if response['status'] > 399:
                self.add_violation(
                    key='broken.img',
                    title='Image not found.',
                    description="The image in '%s' could not be found or took more than 10 seconds to load." % src,
                    points=50
                )
            else:
                results[src] = response

        return results
