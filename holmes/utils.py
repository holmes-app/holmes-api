#!/usr/bin/python
# -*- coding: utf-8 -*-

from six.moves.urllib.parse import urlparse

EMPTY_DOMAIN_RESULT = ('', '')


def get_domain_from_url(url, default_scheme='http'):
    if not url:
        return EMPTY_DOMAIN_RESULT

    scheme = default_scheme
    result = urlparse(url)
    domain = result.netloc

    if (result.scheme and result.scheme in ['http', 'https']):
        scheme = result.scheme

    if (result.scheme and result.scheme not in ['http', 'https']) and not domain:
        domain = result.scheme
    else:
        if not domain:
            domain = result.path.split('/')[0]
            if not '.' in domain:
                return EMPTY_DOMAIN_RESULT

        if ':' in domain:
            domain = domain.split(':')[0]

    original_domain = domain.strip()
    domain = original_domain.replace('www.', '')

    return domain, '%s://%s/' % (scheme, original_domain)
