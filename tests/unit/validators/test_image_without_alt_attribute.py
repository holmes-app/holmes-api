#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from tests.unit.base import ValidatorTestCase
from holmes.reviewer import Reviewer
from holmes.validators.image_without_alt_attribute import (
    ImageWithoutAltAttributeValidator
)
from tests.fixtures import PageFactory, ReviewFactory


class TestImageWithoutAltAttributeValidator(ValidatorTestCase):

    def test_can_validate_image_without_alt_attribute_on_globo_html(self):
        config = Config()

        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=config,
            validators=[]
        )

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = ImageWithoutAltAttributeValidator(reviewer)
        validator.add_fact = Mock()
        validator.add_violation = Mock()
        validator.validate()

        expect(validator.add_violation.call_args_list).to_include(
            call(key='invalid.images.alt',
                 title='Image(s) without alt attribute',
                 description='Images without alt text are not good for Search Engines. Images without alt were found for: <a href="http://ads.globo.com/RealMedia/ads/adstream_nx.ads/globo.com/globo.com/home/@x19" target="_blank">@x19</a>, <a href="http://ads.globo.com/RealMedia/ads/adstream_nx.ads/globo.com/globo.com/home/@Top1" target="_blank">@Top1</a>, <a href="http://ads.globo.com/RealMedia/ads/adstream_nx.ads/globo.com/globo.com/home@Middle" target="_blank">home@Middle</a>, <a href="http://ads.globo.com/RealMedia/ads/adstream_nx.ads/globo.com/globo.com/home/@x20" target="_blank">@x20</a>, <a href="http://ads.globo.com/RealMedia/ads/adstream_nx.ads/globo.com/globo.com/home/@x85" target="_blank">@x85</a>.',
                 points=100))
