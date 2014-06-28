#!/usr/bin/env python
# -*- coding: utf-8 -*-

from holmes.search_providers.elastic import ElasticSearchProvider
from holmes.utils import load_classes


class AuthNZElasticSearchProvider(ElasticSearchProvider):
    def __init__(self, config, db=None, authnz_wrapper=None, io_loop=None):

        if not authnz_wrapper:
            raise Exception('An authentication/authorization wrapper must be defined!')

        super(AuthNZElasticSearchProvider, self).__init__(config, db, io_loop)

        self.syncES.session = authnz_wrapper.sync_client

        self.asyncES.client = authnz_wrapper.async_client

    @classmethod
    def new_instance(cls, config):
        authnz_wrapper_list = load_classes(default=[config.AUTHNZ_WRAPPER])
        if isinstance(authnz_wrapper_list, list) and len(authnz_wrapper_list) == 1:
            authnz_wrapper_class = authnz_wrapper_list.pop()
        else:
            raise Exception('An authentication/authorization wrapper must be defined!')

        authnz_wrapper = authnz_wrapper_class(config)

        return AuthNZElasticSearchProvider(
            config=config,
            authnz_wrapper=authnz_wrapper
        )


if __name__ == '__main__':
    AuthNZElasticSearchProvider.main()
