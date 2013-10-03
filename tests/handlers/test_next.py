from datetime import datetime, timedelta
from ujson import loads

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Page, Review
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestNextHandler(ApiTestCase):
    @gen_test
    def test_next_review_without_page(self):
        yield Page.objects.delete()

        response = yield self.http_client.fetch(
            self.get_url('/next')
        )

        returned_json = loads(response.body)
        expect(returned_json).to_be_null()

    @gen_test
    def test_get_next_review(self):
        yield Page.objects.delete()

        domain = yield DomainFactory.create()

        yesterday = datetime.now() - timedelta(1)

        page = yield PageFactory.create(domain=domain, added_date=yesterday, updated_date=yesterday)

        response = yield self.http_client.fetch(
            self.get_url('/next')
        )

        returned_json = loads(response.body)
        expect(returned_json).not_to_be_null()

        expect(returned_json['uuid']).not_to_be_null()
        review = Review.objects.get(returned_json['uuid'])

        expect(returned_json['page']).not_to_be_null()

        expect(review.page).to_equal(page)


