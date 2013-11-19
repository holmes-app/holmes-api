#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml
from mock import Mock
from tests.unit.base import ApiTestCase

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.links_with_rel_nofollow import (
    LinkWithRelNofollowValidator
)
from tests.fixtures import PageFactory


class TestLinkWithRelNofollowValidator(ApiTestCase):

    def test_validator(self):

        config = Config()

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=config,
            validators=[]
        )

        url = 'http://my-site.com/test.html'

        content = '<html><a href="%s" rel="nofollow">Test</a></html>' % url

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = LinkWithRelNofollowValidator(reviewer)
        validator.add_violation = Mock()

        validator.review.data = {
            'page.all_links': [{'href': url, 'rel': 'nofollow'}]
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='invalid.links.nofollow',
            title='Links with rel="nofollow"',
            description='Links with rel="nofollow" to the same '
                        'domain as the page make it harder for search '
                        'engines to crawl the website. Links with '
                        'rel="nofollow" were found for hrefs ('
                        '<a href="%s" target="_blank">#1</a>).' % url,
            points=10)
