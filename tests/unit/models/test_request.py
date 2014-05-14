#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
from preggy import expect

from tests.unit.base import ApiTestCase
from tests.fixtures import RequestFactory, DomainFactory

from holmes.models import Request
from holmes.config import Config


class TestRequest(ApiTestCase):

    def test_can_create_request(self):
        request = RequestFactory.create()

        expect(str(request)).to_equal('http://g1.globo.com (301)')

        expect(request.id).not_to_be_null()
        expect(request.domain_name).to_equal('g1.globo.com')
        expect(request.url).to_equal('http://g1.globo.com')
        expect(request.effective_url).to_equal('http://g1.globo.com/')
        expect(request.status_code).to_equal(301)
        expect(request.response_time).to_equal(0.23)
        expect(request.completed_date).to_equal(date(2013, 2, 12))
        expect(request.review_url).to_equal('http://globo.com/')

    def test_can_convert_request_to_dict(self):
        request = RequestFactory.create()

        request_dict = request.to_dict()

        expect(request_dict['domain_name']).to_equal(str(request.domain_name))
        expect(request_dict['url']).to_equal(request.url)
        expect(request_dict['effective_url']).to_equal(request.effective_url)
        expect(request_dict['status_code']).to_equal(request.status_code)
        expect(request_dict['response_time']).to_equal(request.response_time)
        expect(request_dict['completed_date']).to_equal(request.completed_date)
        expect(request_dict['review_url']).to_equal(request.review_url)

    def test_can_get_status_code_info(self):
        request = RequestFactory.create(domain_name='g1.globo.com')

        loaded = Request.get_status_code_info('g1.globo.com', self.db)

        expect(loaded[0].get('code')).to_equal(request.status_code)
        expect(loaded[0].get('total')).to_equal(1)

        invalid_domain = Request.get_status_code_info('g2.globo.com', self.db)
        expect(invalid_domain).to_equal([])

    def test_can_get_requests_by_status_code(self):
        request = RequestFactory.create(
            domain_name='globo.com',
            status_code=200
        )

        loaded = Request.get_requests_by_status_code('globo.com', 200, self.db)

        expect(loaded[0].url).to_equal(request.url)
        expect(loaded[0].review_url).to_equal(request.review_url)
        expect(loaded[0].completed_date).to_equal(request.completed_date)

        invalid_domain = Request.get_requests_by_status_code(
            'g1.globo.com',
            200,
            self.db
        )
        expect(invalid_domain).to_equal([])

        invalid_code = Request.get_requests_by_status_code(
            'globo.com',
            2300,
            self.db
        )
        expect(invalid_code).to_equal([])

    def test_can_get_requests_by_status_count(self):
        for i in range(4):
            RequestFactory.create(domain_name='globo.com', status_code=200)

        total = Request.get_requests_by_status_count(
            'globo.com',
            200,
            self.db
        )
        expect(total).to_equal(4)

        invalid_domain = Request.get_requests_by_status_code(
            'g1.globo.com',
            200,
            self.db
        )
        expect(invalid_domain).to_equal([])

        invalid_code = Request.get_requests_by_status_code(
            'globo.com',
            2300,
            self.db
        )
        expect(invalid_code).to_equal([])

    def test_can_get_requests_count_by_status_in_period_of_days(self):
        utcnow = datetime.utcnow()

        DomainFactory.create(name='globo.com')
        DomainFactory.create(name='globoesporte.com')
        DomainFactory.create(name='domain3.com')

        for i in range(3):
            RequestFactory.create(
                status_code=200,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globo.com'
            )
            RequestFactory.create(
                status_code=404,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globo.com'
            )
            RequestFactory.create(
                status_code=404,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globoesporte.com'
            )
            RequestFactory.create(
                status_code=599,
                completed_date=utcnow.date() - timedelta(days=i),
            )

        self.db.flush()

        one_day_ago = utcnow - timedelta(days=1)
        counts = Request.get_requests_count_by_status_in_period_of_days(
            self.db, one_day_ago
        )
        expect(counts).to_equal(
            {'_all': [(200L, 2L), (404L, 4L)],
             u'globo.com': [(200L, 2L), (404L, 2L)],
             u'domain3.com': [],
             u'globoesporte.com': [(404L, 2L)]}
        )

    def test_can_remove_old_requests(self):
        self.db.query(Request).delete()

        config = Config()
        config.DAYS_TO_KEEP_REQUESTS = 1

        for i in range(4):
            RequestFactory.create(
                url='http://m.com/page-%d' % i,
                domain_name='m.com',
                status_code=200,
                completed_date=date.today() - timedelta(days=i)
            )

        Request.delete_old_requests(self.db, config)

        requests = self.db.query(Request).all()
        expect(requests).to_length(1)

    def test_can_get_all_status_code(self):
        self.db.query(Request).delete()

        for i in range(4):
            RequestFactory.create(
                url='http://m.com/page-%d' % i,
                domain_name='m.com',
                status_code=200 + (100*i),
                completed_date=date.today() - timedelta(days=i)
            )

        status_code = Request.get_all_status_code(self.db)

        expect(status_code).to_length(4)

        expect(status_code).to_be_like([
            {
                'statusCodeTitle': 'OK',
                'statusCode': 200
            }, {
                'statusCodeTitle': 'Multiple Choices',
                'statusCode': 300
            }, {
                'statusCodeTitle': 'Bad Request',
                'statusCode': 400
            }, {
                'statusCodeTitle': 'Internal Server Error',
                'statusCode': 500
            }
        ])
