#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging

from holmes.facters import Facter


class ImageFacter(Facter):
    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.images': {
                'title': 'Images',
                'description': lambda value: list(value),
                'unit': 'images',
                'category': 'Static',
            },
            'total.size.img': {
                'title': 'Total images size',
                'description': lambda value: '%d' % value,
                'unit': 'kb',
                'category': 'SEO',
            },
            'total.requests.img': {
                'title': 'Total images requests',
                'description': lambda value: value,
                'category': 'HTTP',
                'unit': 'number'
            }
        }

    def looks_like_base64(self, url):
        if url.lstrip().startswith('data:image'):
            return True
        return False

    def get_facts(self):
        img_files = self.get_images()

        self.review.data['page.images'] = set()
        self.review.data['total.size.img'] = 0

        self.add_fact(
            key='page.images',
            value=set()
        )

        self.add_fact(
            key='total.size.img',
            value=0
        )

        images_to_get = set()
        images_without_base64 = []

        for img_file in img_files:
            src = img_file.get('src')
            if not src:
                continue

            if self.looks_like_base64(src):
                continue

            images_without_base64.append(img_file)

            src = self.normalize_url(src)
            if src:
                images_to_get.add(src)

        self.review.data['page.all_images'] = images_without_base64

        for src in images_to_get:
            self.async_get(src, self.handle_url_loaded)

        self.add_fact(
            key='total.requests.img',
            value=len(images_to_get)
        )

    def handle_url_loaded(self, url, response):
        logging.debug('Got response (%s) from %s!' % (response.status_code,
                                                      url))

        size_img = 0
        if response.text:
            size_img = len(response.text) / 1024.0

        self.review.facts['page.images']['value'].add(url)
        self.review.data['page.images'].add((url, response))

        self.review.facts['total.size.img']['value'] += size_img
        self.review.data['total.size.img'] += size_img

    def get_images(self):
        return self.reviewer.current_html.cssselect(':not(script) img[src]')
