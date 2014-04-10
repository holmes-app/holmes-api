#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.concurrent import return_future


class SearchProvider(object):
    def __init__(self, config, db, io_loop=None):
        raise NotImplementedError()

    def index_review(self, review):
        raise NotImplementedError()

    @return_future
    def get_by_violation_key_name(self, key_id, current_page=1, page_size=10, domain=None, page_filter=None, callback=None):
        raise NotImplementedError()

    @return_future
    def get_domain_active_reviews(self, domain, current_page=1, page_size=10, page_filter=None, callback=None):
        raise NotImplementedError()

    @classmethod
    def argparser(cls):
        import argparse

        parser = argparse.ArgumentParser(description='Setup Holmes index on an ElasticSearch server')
        parser.add_argument(
            '-c', '--conf',
            nargs=1,
            metavar='conf_file',
            help='path to configuration file'
        )
        parser.add_argument(
            '-s', '--server',
            nargs=1,
            metavar='host:port',
            help='elastic search server host and port'
        )
        parser.add_argument(
            '-i', '--index',
            nargs=1,
            metavar='index_name',
            help='name of the index'
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='create the index'
        )
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='recreate the index (use with caution)'
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='delete the index (use with caution)'
        )
        parser.add_argument(
            '-k', '--keys',
            nargs='+',
            metavar='key',
            help='index reviews with violation of such keys'
        )
        parser.add_argument(
            '-a', '--all-keys',
            action='store_true',
            help='index all reviews with at least one violation of any key (might take long)'
        )
        parser.add_argument(
            '-r', '--replace',
            action='store_true',
            help='replace entire index (default is increment/resume)'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='count',
            default=0,
            help='log level: v=warning, vv=info, vvv=debug'
        )

        return parser

    @classmethod
    def main(cls):
        raise NotImplementedError()

if __name__ == '__main__':
    SearchProvider.main()
