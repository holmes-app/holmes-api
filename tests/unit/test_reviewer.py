#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import uuid4

import requests
import lxml.html
from preggy import expect
from mock import patch, Mock
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError, InvalidSchema

from holmes.reviewer import Reviewer, InvalidReviewError
from holmes.config import Config
from holmes.validators.base import Validator
from tests.unit.base import ApiTestCase


class TestReview(ApiTestCase):
    def get_reviewer(
            self, api_url=None, page_uuid=None, page_url='http://page.url',
            review_uuid=None, config=None, validators=[Validator]):

        if api_url is None:
            api_url = self.get_url('/')

        if page_uuid is None:
            page_uuid = uuid4()

        if review_uuid is None:
            review_uuid = uuid4()

        if config is None:
            config = Config()

        return Reviewer(
            api_url=api_url,
            page_uuid=page_uuid,
            page_url=page_url,
            review_uuid=review_uuid,
            config=config,
            validators=validators
        )

    def test_can_create_reviewer(self):
        page_uuid = uuid4()
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid, config=config, validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.review_uuid).to_equal(review_uuid)
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_can_create_reviewer_with_page_string_uuid(self):
        page_uuid = uuid4()
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=str(page_uuid),
                                     review_uuid=review_uuid,
                                     config=config,
                                     validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.review_uuid).to_equal(review_uuid)
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_can_create_reviewer_with_review_string_uuid(self):
        page_uuid = uuid4()
        review_uuid = uuid4()
        config = Config()
        validators = [Validator]
        reviewer = self.get_reviewer(page_uuid=page_uuid,
                                     review_uuid=str(review_uuid),
                                     config=config,
                                     validators=validators)

        expect(reviewer.page_uuid).to_equal(page_uuid)
        expect(reviewer.page_url).to_equal('http://page.url')
        expect(reviewer.review_uuid).to_equal(review_uuid)
        expect(reviewer.config).to_equal(config)
        expect(reviewer.validators).to_equal(validators)

    def test_reviewer_fails_if_wrong_config(self):
        try:
            self.get_reviewer(config='wrong config object')
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('config argument must be an instance of holmes.config.Config')
        else:
            assert False, 'Should not have gotten this far'

    def test_reviewer_fails_if_wrong_validators(self):
        validators = [Validator, "wtf"]
        validators2 = [Validator, Config]

        try:
            self.get_reviewer(validators=validators)
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('All validators must subclass holmes.validators.base.Validator')
        else:
            assert False, 'Should not have gotten this far'

        try:
            self.get_reviewer(validators=validators2)
        except AssertionError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of('All validators must subclass holmes.validators.base.Validator')
        else:
            assert False, 'Should not have gotten this far'

    def test_load_content_raises_when_invalid_status_code(self):
        page_url = 'http://page.url'
        reviewer = self.get_reviewer()

        reviewer.responses[page_url] = {
            'status': 500,
            'content': '',
            'html': None
        }

        try:
            reviewer.load_content()
        except InvalidReviewError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of("Could not load 'http://page.url'!")
        else:
            assert False, 'Should not have gotten this far'

    @patch('requests.get')
    def test_get_response_fills_dict(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='<p>OK</p>', content='<p>OK</p>')
        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)

        reviewer.get_response(page_url)

        expect(reviewer.responses).to_include(page_url)
        expect(reviewer.responses[page_url]['status']).to_equal(200)
        expect(reviewer.responses[page_url]['content']).to_include('OK')

        expect(reviewer.responses[page_url]['html']).not_to_be_null()
        expect(reviewer.responses[page_url]['html']).to_be_instance_of(lxml.html.HtmlElement)

    @patch('requests.get')
    def test_get_response_fills_empty_dict_when_error(self, mock_get):
        mock_get.side_effect = Exception

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)

        result = reviewer.get_response(page_url)

        expect(result['status']).to_equal(404)
        expect(result['content']).to_equal('')
        expect(result['html']).to_be_null()

    @patch('requests.get')
    def test_get_response_fills_html_when_200(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='<p>OK</p>')

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)

        result = reviewer.get_response(page_url)

        expect(result['status']).to_equal(200)
        expect(result['content']).not_to_be_null()
        expect(result['html']).not_to_be_null()
        expect(result['html'].text_content()).to_equal('OK')

    @patch('requests.get')
    def test_get_response_add_violation_when_empty_document(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text='</html>')

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)
        reviewer.add_violation = Mock()

        result = reviewer.get_response(page_url)

        expect(result['status']).to_equal(200)
        expect(result['content']).not_to_be_null()
        expect(result['html']).to_be_null()
        expect(reviewer.add_violation.called).to_be_true()

    @patch('requests.get')
    def test_get_response_add_violation_when_invalid_html(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text=' ')

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)
        reviewer.add_violation = Mock()

        result = reviewer.get_response(page_url)

        expect(result['status']).to_equal(200)
        expect(result['content']).not_to_be_null()
        expect(result['html']).to_be_null()
        expect(reviewer.add_violation.called).to_be_true()

    @patch('requests.get')
    def test_get_response_do_not_fills_html_when_404(self, mock_get):
        mock_get.return_value = Mock(status_code=404, text='Error')

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url)

        result = reviewer.get_response(page_url)

        expect(result['status']).to_equal(404)
        expect(result['content']).not_to_be_null()
        expect(result['html']).to_be_null()

    def test_review_calls_validators(self):
        test_class = {}

        class MockValidator(Validator):
            def validate(self):
                test_class['has_validated'] = True

        page_url = 'http://www.google.com'
        reviewer = self.get_reviewer(page_url=page_url, validators=[MockValidator])

        reviewer.responses[page_url] = {
            'status': 200,
            'content': '<html><head></head><body></body></html>',
            'html': None
        }

        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            reviewer.review()

        expect(test_class['has_validated']).to_be_true()

    def test_reviewer_add_fact(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            reviewer.add_fact('key', 'value', 'title', 'unit')

            post_mock.assert_called_once_with(
                '%s/page/%s/review/%s/fact' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                data={'unit': 'unit', 'value': 'value', 'key': 'key', 'title':'title'}
            )

    def test_reviewer_add_fact_fails_if_wrong_status(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=400, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.add_fact('key', 'value', 'title', 'unit')
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    "Could not add fact 'key' to review %s! Status Code: 400, Error: OK" % review_uuid
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_reviewer_add_fact_fails_connection_error(self):
        with patch.object(requests, 'post') as post_mock:
            post_mock.side_effect = ConnectionError

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.add_fact('key', 'value', 'title', 'unit')
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    "Could not add fact 'key' to review %s! ConnectionError - %s" % (
                        review_uuid,
                        '%s/page/%s/review/%s/fact' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                        )
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_reviewer_add_violation(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            reviewer.add_violation('key', 'title', 'description', 100)

            post_mock.assert_called_once_with(
                '%s/page/%s/review/%s/violation' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                data={'key': 'key', 'title': 'title', 'description': 'description', 'points': 100}
            )

    def test_reviewer_add_violation_fails_if_wrong_status(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=400, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.add_violation('key', 'title', 'description', 100)
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    "Could not add violation 'key' to review %s! Status Code: 400, Error: OK" % review_uuid
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_reviewer_add_violation_fails_connection_error(self):
        with patch.object(requests, 'post') as post_mock:
            post_mock.side_effect = ConnectionError

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.add_violation('key', 'title', 'description', 100)
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    "Could not add violation 'key' to review %s! ConnectionError - %s" % (
                        review_uuid,
                        '%s/page/%s/review/%s/violation' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                        )
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_reviewer_complete(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=200, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            reviewer.complete()

            post_mock.assert_called_once_with(
                '%s/page/%s/review/%s/complete' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                data={}
            )

    def test_reviewer_complete_fails_if_wrong_status(self):
        with patch.object(requests, 'post') as post_mock:
            response_mock = Mock(status_code=400, text='OK')
            post_mock.return_value = response_mock

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.complete()
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    'Could not complete review %s! Status Code: 400, Error: OK' % review_uuid
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_reviewer_complete_fails_connection_error(self):
        with patch.object(requests, 'post') as post_mock:
            post_mock.side_effect = ConnectionError

            page_uuid = uuid4()
            review_uuid = uuid4()

            reviewer = self.get_reviewer(page_uuid=page_uuid, review_uuid=review_uuid)

            try:
                reviewer.complete()
            except InvalidReviewError:
                err = sys.exc_info()[1]
                expect(err).to_have_an_error_message_of(
                    "Could not complete review %s! ConnectionError - %s" % (
                        review_uuid,
                        '%s/page/%s/review/%s/complete' % (reviewer.api_url.rstrip('/'), page_uuid, review_uuid),
                        )
                )
            else:
                assert False, 'Should not have gotten this far'

    def test_can_get_current(self):
        reviewer = self.get_reviewer()

        reviewer.responses[reviewer.page_url] = {
            'status': 200,
            'content': '',
            'html': None
        }

        response = reviewer.current
        expect(response).not_to_be_null()
        expect(response['status']).to_equal(200)

    @patch('requests.get')
    def test_can_get_current_when_not_loaded(self, mock_get):
        reviewer = self.get_reviewer()

        expect(reviewer.page_url in reviewer.responses).to_be_false()
        mock_get.return_value = Mock(status_code=200, text='OK')
        reviewer.current
        expect(reviewer.page_url in reviewer.responses).to_be_true()

    def test_can_get_status_code(self):
        reviewer = self.get_reviewer()
        page_url = 'http://google.com'
        expect(reviewer.status_codes).to_length(0)
        reviewer.get_status_code(page_url)
        expect(reviewer.status_codes).to_length(1)
        expect(reviewer.status_codes[page_url]).not_to_be_null()

    def test_can_get_status_code_when_already_got_before(self):
        reviewer = self.get_reviewer()
        page_url = 'http://google.com'

        reviewer.get_status_code(page_url)
        expect(reviewer.status_codes).to_length(1)
        expect(reviewer.status_codes[page_url]).not_to_be_null()

        reviewer.get_status_code(page_url)
        expect(reviewer.status_codes).to_length(1)

    @patch("requests.request")
    def test_can_get_status_code_fail_http_error(self, mock_request):
        mock_request.side_effect = HTTPError
        reviewer = self.get_reviewer()
        reviewer.get_status_code(reviewer.page_url)
        expect(reviewer.status_codes[reviewer.page_url]).to_equal(404)

    @patch("requests.request")
    def test_can_get_status_code_fail_timeout(self, mock_request):
        mock_request.side_effect = Timeout
        reviewer = self.get_reviewer()
        reviewer.get_status_code(reviewer.page_url)
        expect(reviewer.status_codes[reviewer.page_url]).to_equal(404)

    @patch("requests.request")
    def test_can_get_status_code_fail_too_many_redirects(self, mock_request):
        mock_request.side_effect = TooManyRedirects
        reviewer = self.get_reviewer()
        reviewer.get_status_code(reviewer.page_url)
        expect(reviewer.status_codes[reviewer.page_url]).to_equal(404)

    @patch("requests.request")
    def test_can_get_status_code_fail_connection_error(self, mock_request):
        mock_request.side_effect = ConnectionError
        reviewer = self.get_reviewer()
        reviewer.get_status_code(reviewer.page_url)
        expect(reviewer.status_codes[reviewer.page_url]).to_equal(404)

    @patch("requests.request")
    def test_can_get_status_code_fail_invalid_schema(self, mock_request):
        mock_request.side_effect = InvalidSchema
        reviewer = self.get_reviewer()
        reviewer.get_status_code(reviewer.page_url)
        expect(reviewer.status_codes[reviewer.page_url]).to_equal(404)

    def test_enqueue_when_none(self):
        reviewer = self.get_reviewer()
        enqueue = reviewer.enqueue()
        expect(enqueue).to_be_null()

    @patch('requests.post')
    def test_can_enqueue_one_url(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='OK')
        reviewer = self.get_reviewer()
        reviewer.enqueue('http://globo.com')
        mock_post.assert_called_once_with(
            '%spage' % reviewer.api_url,
            data={'url': 'http://globo.com', 'origin_uuid': str(reviewer.page_uuid)}
            )

    @patch('requests.post')
    def test_can_enqueue_multiple_urls(self, mock_post):
        mock_post.return_value = Mock(status_code=200, text='OK')
        reviewer = self.get_reviewer()
        reviewer.enqueue('http://globo.com', 'http://g1.globo.com')
        mock_post.assert_called_once_with(
            '%spages' % reviewer.api_url,
            data={'url': ('http://globo.com', 'http://g1.globo.com'),
                  'origin_uuid': str(reviewer.page_uuid)}
            )

    @patch('requests.post')
    def test_enqueue_404(self, mock_post):
        mock_post.return_value = Mock(status_code=404, text='Not Found')
        reviewer = self.get_reviewer()
        try:
            reviewer.enqueue('http://globo.com')
        except InvalidReviewError:
            err = sys.exc_info()[1]
            expect(err).to_have_an_error_message_of(
                "Could not enqueue page 'http://globo.com'! Status Code: 404, Error: Not Found")
        else:
            assert False, 'Should not have gotten this far'
