#!/usr/bin/python
# -*- coding: utf-8 -*-


from holmes.validators.base import Validator


class ImageRequestsValidator(Validator):
    def validate(self):
        img_files = self.get_img_requests()

        self.add_fact(
            key='total.requests.img',
            value=len(img_files)
        )

        results = self.process_img_requests(img_files)

        total_size = 0
        total_size_gzip = 0
        for item in results.values():
            if item:
                size_img = len(item['content']) / 1024.0
                size_img_gzip = len(self.to_gzip(item['content'])) / 1024.0
                total_size += size_img
                total_size_gzip += size_img_gzip

                if size_img_gzip > self.reviewer.config.MAX_KB_SINGLE_IMAGE_AFTER_GZIP:
                    self.add_violation(
                        key='single.size.img',
                        title='Single image size in kb is too big.',
                        description='Found a image bigger then limit %d (%d over limit): %s' % (
                            self.reviewer.config.MAX_KB_SINGLE_IMAGE_AFTER_GZIP, size_img_gzip - self.reviewer.config.MAX_KB_SINGLE_IMAGE_AFTER_GZIP, item
                        ),
                        points=size_img_gzip - self.reviewer.config.MAX_KB_SINGLE_IMAGE_AFTER_GZIP
                    )

        self.add_fact(
            key='total.size.img',
            value=total_size,
            unit='kb'
        )

        self.add_fact(
            key='total.size.img.gzipped',
            value=total_size_gzip,
            unit='kb'
        )

        if len(img_files) > self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE:
            self.add_violation(
                key='total.requests.img',
                title='Too many image requests.',
                description='This page has %d images request (%d over limit). Having too many requests impose a tax in the browser due to handshakes.' % (
                    len(img_files), len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE
                ),
                points=5 * (len(img_files) - self.reviewer.config.MAX_IMG_REQUESTS_PER_PAGE)
            )

        if total_size_gzip > self.reviewer.config.MAX_IMG_KB_PER_PAGE_AFTER_GZIP:
            self.add_violation(
                key='total.size.img',
                title='Total image size in kb is too big.',
                description="There's %.2fkb of Images in this page and that adds up to more download time slowing down the page rendering to the user." % total_size_gzip,
                points=int(total_size_gzip - self.reviewer.config.MAX_IMG_KB_PER_PAGE_AFTER_GZIP)
            )

    def get_img_requests(self):
        return self.reviewer.current['html'].cssselect('img[src]')

    def process_img_requests(self, img_files):
        results = {}
        for img_file in img_files:
            src = img_file.get('src')
            results[src] = self.get_response(src)

        return results
