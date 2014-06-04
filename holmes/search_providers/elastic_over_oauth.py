#!/usr/bin/env python
# -*- coding: utf-8 -*-

from holmes.authnz import AuthNZ
from holmes.search_providers.elastic import ElasticSearchProvider


class ElasticOverOAuthSearchProvider(ElasticSearchProvider):
    def __init__(self, config, db=None, authNZ=None, io_loop=None):
        super(ElasticOverOAuthSearchProvider, self).__init__(config, db, io_loop)

        self.syncES.session = authNZ.oAuthSyncClient

        self.asyncES.client = authNZ.oAuthAsyncClient

    @classmethod
    def new_instance(cls, config):
        authNZ = AuthNZ(config)
        return ElasticOverOAuthSearchProvider(config=config, authNZ=authNZ)


if __name__ == '__main__':
    ElasticOverOAuthSearchProvider.main()
