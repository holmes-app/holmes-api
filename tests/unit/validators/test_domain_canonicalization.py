#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.domain_canonicalization import (
    DomainCanonicalizationValidator)
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestDomainCanonicalizationValidator(ValidatorTestCase):

    @staticmethod
    def get_validator_for_url(url=None):
        page = PageFactory.create()
        if url:
            page.url = url
        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )
        return DomainCanonicalizationValidator(reviewer)

    def test_can_validate_page_url_not_root(self):
        validator = self.get_validator_for_url('http://globo.com/abcd')
        validator.async_get = Mock()
        validator.get_canonical_urls = Mock()
        expect(validator.validate()).to_equal(None)
        expect(validator.async_get.called).to_be_false()
        expect(validator.get_canonical_urls.called).to_be_false()

    def test_get_canonical_urls_call(self):
        url = 'http://globo.com/'
        validator = self.get_validator_for_url(url)
        expected = {'www_url': 'http://www.globo.com',
                    'no_www_url': 'http://globo.com'}
        expect(validator.get_canonical_urls()).to_equal(expected)
        url = 'http://www.globo.com/'
        validator = self.get_validator_for_url(url)
        expected = {'www_url': 'http://www.globo.com',
                    'no_www_url': 'http://globo.com'}
        expect(validator.get_canonical_urls()).to_equal(expected)

    def test_can_validate_async_calls(self):
        url = 'http://globo.com/'
        validator = self.get_validator_for_url(url)
        validator.async_get = Mock()
        validator.reviewer.wait_for_async_requests = Mock()
        validator.has_same_effective_urls = Mock()
        validator.has_redirect_violation = Mock()
        validator.add_violation = Mock()
        validator.validate()
        expect(validator.async_get.call_count).to_equal(2)
        expect(validator.async_get.call_args_list).to_include(
            call('http://globo.com', validator.handle_no_www_url_res, follow_redirects=False)
        )
        expect(validator.async_get.call_args_list).to_include(
            call('http://www.globo.com', validator.handle_www_url_res,
                 follow_redirects=False)
        )

    def test_handle_async_get_response(self):
        url = 'http://globo.com'
        validator = self.get_validator_for_url(url)
        expected_response = Mock(
            status_code=200,
            effective_url='http://globo.com/'
        )
        expected = ('http://globo.com', expected_response)
        validator.handle_no_www_url_res(*expected)
        expect(validator.no_www_url_res).to_equal(expected_response)
        expected_response = Mock(
            status_code=301,
            effective_url='http://globo.com/',
            headers={
                'Location': 'http://www.globo.com/'
            }
        )
        expected = ('http://www.globo.com', expected_response)
        validator.handle_www_url_res(*expected)
        expect(validator.www_url_res).to_equal(expected_response)

    def test_has_same_effective_urls(self):
        validator = self.get_validator_for_url()

        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            status_code=301, effective_url='http://globo.com/',
            headers={'Location': 'http://www.globo.com/'})
        expect(validator.has_same_effective_urls()).to_equal(True)

        validator.www_url_res = Mock(
            status_code=301, effective_url='http://www.globo.com/',
            headers={'Location': 'http://globo.com/'})
        validator.no_www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://globo.com/')
        expect(validator.has_same_effective_urls()).to_equal(True)

        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://globo.com/')
        expect(validator.has_same_effective_urls()).to_equal(False)

    def test_has_redirect_error(self):
        validator = self.get_validator_for_url()
        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={'Location': 'http://www.globo.com/'},
            status_code=302, effective_url='http://globo.com/')
        expect(validator.has_redirect_violation()).to_equal(validator.no_www_url_res)

        validator.www_url_res = Mock(
            headers={'Location': 'http://globo.com/'},
            status_code=302, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://globo.com/')
        expect(validator.has_redirect_violation()).to_equal(validator.www_url_res)

        validator.www_url_res = Mock(
            headers={'Location': 'http://globo.com/'},
            status_code=301, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://globo.com/')
        expect(validator.has_redirect_violation()).to_equal(None)

    def test_call_add_violation(self):
        url = 'http://globo.com/'
        validator = self.get_validator_for_url(url)
        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            status_code=301, effective_url='http://globo.com/',
            headers={'Location': 'http://www.globo.com/'})
        validator.async_get = Mock()
        validator.reviewer.wait_for_async_requests = Mock()
        validator.add_violation = Mock()
        validator.validate()
        expect(validator.add_violation.called).to_be_false()

        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://globo.com/')
        validator.add_violation = Mock()
        validator.validate()
        expect(validator.add_violation.called).to_be_true()
        validator.add_violation.assert_called_once_with(
            key='page.canonicalization.different_endpoints',
            value={
                'www_url': 'http://www.globo.com',
                'no_www_url': 'http://globo.com',
            },
            points=50
        )

        validator.www_url_res = Mock(
            headers={},
            status_code=200, effective_url='http://www.globo.com/')
        validator.no_www_url_res = Mock(
            headers={'Location': 'http://www.globo.com/'},
            status_code=302, effective_url='http://globo.com/')
        validator.add_violation = Mock()
        validator.validate()
        expect(validator.add_violation.called).to_be_true()
        validator.add_violation.assert_called_once_with(
            key='page.canonicalization.no_301_redirect',
            value=validator.no_www_url_res,
            points=50
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = DomainCanonicalizationValidator(reviewer)
        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(2)
        expect('page.canonicalization.different_endpoints'
               in definitions).to_be_true()
        expect('page.canonicalization.no_301_redirect'
               in definitions).to_be_true()

        diff_endpoints_desc = definitions['page.canonicalization.different_endpoints']['description']
        expect(diff_endpoints_desc % {
            'no_www_url': 'http://globo.com/',
            'www_url': 'http://www.globo.com/'
        }).to_equal(
            'This page have the canonical url`s "http://globo.com/" '
            'and "http://www.globo.com/" with '
            'different endpoints. This both url`s should point '
            'to the same location. '
            'Not fixing this may cause search engines to be unsure as '
            'to which URL is the correct one to index.'
        )

        value = {
            'headers': {'Location': 'http://www.globo.com/'},
            'status_code': 302,
            'effective_url': 'http://globo.com/'
        }
        no_301_red = definitions['page.canonicalization.no_301_redirect']
        no_301_red_desc = no_301_red['description']
        no_301_red_value_parser = no_301_red['value_parser']
        expect(no_301_red_desc % no_301_red_value_parser(value)).to_equal(
            'This Canonical url "http://globo.com/" is redirecting to '
            '"http://www.globo.com/" with a different than 301 status code: 302. '
            'This may cause search engines to be unsure to where the URL is '
            'being redirected.'
        )
