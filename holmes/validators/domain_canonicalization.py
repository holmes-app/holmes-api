#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.utils import is_valid
from holmes.validators.base import Validator


class DomainCanonicalizationValidator(Validator):

    @classmethod
    def get_different_endpoints_description(cls, value):
        return (
            'This page have the canonical url`s "{}" and "{}" with '
            'different endpoints. This both url`s should point '
            'to the same location. '
            'Not fixing this may cause search engines to be unsure as '
            'to which URL is the correct one to index.'
        ).format(value['no_www_url'], value['www_url'])

    @classmethod
    def get_no_301_description(cls, value):
        return (
            'This Canonical url "{}" is redirecting to "{}" with a different '
            'than 301 status code: {}. This may cause search engines to be '
            'unsure to where the URL is being redirected.'.format(
                value['effective_url'], value['headers']['Location'],
                value['status_code']
            )
        )

    @classmethod
    def get_violation_definitions(cls):
        return {
            'page.canonicalization.different_endpoints': {
                'title': 'Canonical URLs have different endpoints',
                'description': cls.get_different_endpoints_description,
                'category': 'SEO',
                'generic_description': (
                    'Canonical URLs is a couple of URLs with and without '
                    'the \'www\' prefix. For example: site.com and www.site.com '
                    'are canonical URLs. This violation is about a root page with '
                    'your canonical URLs pointing to different endpoints. This '
                    'behavior is down ranked in Search Engines indexing.'
                )
            },
            'page.canonicalization.no_301_redirect': {
                'title': 'Canonical URLs have a non 301 redirect',
                'description': cls.get_no_301_description,
                'category': 'SEO',
                'generic_description': (
                    'Canonical URLs is a couple of URLs with and without '
                    'the \'www\' prefix. For example: site.com and www.site.com '
                    'are canonical URLs. Canonical URLs should point to the '
                    'same points. This violation is about a redirection of one '
                    'of this URLs maked by a non 301 redirection. Redirections '
                    'different than a 301 type may cause search engines to be '
                    'unsure to where the URL is being redirected.'
                )
            }
        }

    def get_canonical_urls(self):
        url = self.reviewer.page_url
        parsed_url = is_valid(url)
        scheme_url = parsed_url.scheme
        domain_url = parsed_url.netloc

        if domain_url.startswith('www.'):
            www_url = url.rstrip('/')
            no_www_url = '{}://{}'.format(scheme_url, domain_url[4:])
        else:
            no_www_url = url.rstrip('/')
            www_url = '{}://www.{}'.format(scheme_url, domain_url)

        return {'www_url': www_url, 'no_www_url': no_www_url}

    def validate(self):
        if not self.reviewer.is_root():
            return

        canonical_urls = self.get_canonical_urls()

        self.async_get(canonical_urls['www_url'],
                       self.handle_www_url_res,
                       follow_redirects=False)
        self.async_get(canonical_urls['no_www_url'],
                       self.handle_no_www_url_res,
                       follow_redirects=False)
        self.reviewer.wait_for_async_requests()

        if not self.has_same_effective_urls():
            self.add_violation(
                key='page.canonicalization.different_endpoints',
                value=canonical_urls,
                points=50
            )
        else:
            redirect_error = self.has_redirect_violation()
            if redirect_error:
                self.add_violation(
                    key='page.canonicalization.no_301_redirect',
                    value=redirect_error,
                    points=50
                )

    def handle_www_url_res(self, url, response):
        self.www_url_res = response

    def handle_no_www_url_res(self, url, response):
        self.no_www_url_res = response

    def has_same_effective_urls(self):
        def target_url(res):
            if res.status_code != 200 and 'Location' in res.headers:
                return res.headers['Location'].rstrip('/')
            else:
                return res.effective_url.rstrip('/')

        return target_url(self.www_url_res) == target_url(self.no_www_url_res)

    def has_redirect_violation(self):
        def test(res):
            return res if (
                'Location' in res.headers
                and res.headers['Location'].rstrip('/')
                    != res.effective_url.rstrip('/')
                and res.status_code != 301
            ) else None

        return test(self.www_url_res) or test(self.no_www_url_res)
