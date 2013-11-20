#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class ImageFacter(Facter):

    def get_facts(self):
        img_files = self.get_images()

        self.review.data['page.all_images'] = img_files
        self.review.data['page.images'] = set()
        self.review.data['total.size.img'] = 0

        self.add_fact(
            key='page.images',
            value=set(),
            title='Images',
            unit='image'
        )

        self.add_fact(
            key='total.size.img',
            value=0,
            unit='kb',
            title='Total images size'
        )

        images_to_get = set()

        for img_file in img_files:
            src = img_file.get('src')
            if not src:
                continue

            is_absolute = self.is_absolute(src)

            if not is_absolute:
                src = self.rebase(src)

            images_to_get.add(src)

        for url in images_to_get:
            self.async_get(url, self.handle_url_loaded)

        self.add_fact(
            key='total.requests.img',
            value=len(images_to_get),
            title='Total images requests'
        )

    def handle_url_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))

        self.review.facts['page.images']['value'].add(url)
        self.review.data['page.images'].add((url, response))

        size_img = len(response.text) / 1024.0
        self.review.facts['total.size.img']['value'] += size_img
        self.review.data['total.size.img'] += size_img

    def get_images(self):
        return self.reviewer.current_html.cssselect(':not(script) img[src]')
