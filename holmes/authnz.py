#!/usr/bin/env python
# -*- coding: utf-8 -*-

from alf.client import Client as OAuthSyncClient
from tornadoalf.client import Client as OAuthAsyncClient


class AuthNZ(object):
    """ This class gathers authentication and authorization
    for some of the services used by Holmes
    """
    def __init__(self, config):
        self.config = config
        self._oAuthSyncClient = None
        self._oAuthAsyncClient = None

    @property
    def oAuthSyncClient(self):
        """Synchronous OAuth 2.0 Bearer client"""
        if not self._oAuthSyncClient:
            self._oAuthSyncClient = OAuthSyncClient(
                token_endpoint=self.config.get('OAUTH_TOKEN_ENDPOINT'),
                client_id=self.config.get('OAUTH_CLIENT_ID'),
                client_secret=self.config.get('OAUTH_CLIENT_SECRET')
            )
        return self._oAuthSyncClient

    @property
    def oAuthAsyncClient(self):
        """Asynchronous OAuth 2.0 Bearer client"""
        if not self._oAuthAsyncClient:
            self._oAuthAsyncClient = OAuthAsyncClient(
                token_endpoint=self.config.get('OAUTH_TOKEN_ENDPOINT'),
                client_id=self.config.get('OAUTH_CLIENT_ID'),
                client_secret=self.config.get('OAUTH_CLIENT_SECRET')
            )
        return self._oAuthAsyncClient
