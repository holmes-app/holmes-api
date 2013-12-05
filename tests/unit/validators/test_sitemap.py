#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.sitemap import SitemapValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory


class TestSitemapValidator(ValidatorTestCase):

    def test_return_if_page_url_is_not_root_of_domain(self):
        page = PageFactory.create(url='http://globo.com/1')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=404, text=None)}
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.call_count).to_equal(0)

    def test_add_violation_when_404(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=404, text=None)}
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='sitemap.not_found',
            value='http://g1.globo.com/sitemap.xml',
            points=100
        )

    def test_add_violation_when_sitemap_is_empty(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='')}
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='sitemap.empty',
            value='http://g1.globo.com/sitemap.xml',
            points=100
        )

    def test_add_violation_when_sitemap_is_too_large(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10241}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': []}
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='total.size.sitemap',
            value={
                'url': 'http://g1.globo.com/sitemap.xml',
                'size': 10.0009765625
            },
            points=10
        )

    def test_add_violation_when_sitemap_has_many_links(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 50001}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': []}
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='total.links.sitemap',
            value={'url': 'http://g1.globo.com/sitemap.xml', 'links': 50001},
            points=10
        )

    def test_add_violation_when_sitemap_has_links_with_no_path(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 20}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': ['http://g1.globo.com/']}
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.call_count).to_equal(0)

    def test_add_violation_when_sitemap_has_links_that_not_need_to_be_encoded(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 20}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': ['http://g1.globo.com/1.html']}
        validator.add_violation = Mock()

        validator.validate()

        expect(validator.add_violation.call_count).to_equal(0)

    def test_add_violation_when_sitemap_has_links_that_need_to_be_encoded(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 20}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': ['http://g1.globo.com/ümlat.php', u'http://g1.globo.com/ümlat.php']}
        validator.add_violation = Mock()
        # validator.send_url = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='sitemap.links.not_encoded',
            value={'url': 'http://g1.globo.com/sitemap.xml', 'links': 2},
            points=10)

    def test_add_violation_when_sitemap_has_links_that_need_to_be_encoded_with_amp(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 20}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': ['http://g1.globo.com/%C3%BCmlat.php&q=name']}
        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='sitemap.links.not_encoded',
            value={'url': 'http://g1.globo.com/sitemap.xml', 'links': 1},
            points=10
        )

    def test_add_violation_when_sitemap_with_good_link(self):
        page = PageFactory.create(url='http://globo.com')

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            validators=[]
        )

        validator = SitemapValidator(reviewer)
        validator.review.data['sitemap.files.size'] = {'http://g1.globo.com/sitemap.xml': 10}
        validator.review.data['sitemap.data'] = {'http://g1.globo.com/sitemap.xml': Mock(status_code=200, text='data', url='http://g1.globo.com/%C3%BCmlat.php&amp;q=name')}
        validator.review.data['sitemap.files.urls'] = {'http://g1.globo.com/sitemap.xml': 20}
        validator.review.data['sitemap.urls'] = {'http://g1.globo.com/sitemap.xml': ['http://g1.globo.com/%C3%BCmlat.php&amp;q=name']}
        validator.add_violation = Mock()
        validator.flush = Mock()

        validator.validate()

        expect(validator.add_violation.call_count).to_equal(0)
        expect(validator.flush.call_count).to_equal(1)

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = SitemapValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect('sitemap.not_found' in definitions).to_be_true()
        expect('sitemap.empty' in definitions).to_be_true()
        expect('total.size.sitemap' in definitions).to_be_true()
        expect('total.links.sitemap' in definitions).to_be_true()
        expect('sitemap.links.not_encoded' in definitions).to_be_true()
