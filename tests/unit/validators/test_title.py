#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock
from preggy import expect
import lxml.html

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.title import TitleValidator
from holmes.models import Key, KeysCategory
from tests.unit.base import ValidatorTestCase
from tests.fixtures import (
    PageFactory, DomainFactory, DomainsViolationsPrefsFactory
)


class TestTitleValidator(ValidatorTestCase):

    def test_can_validate_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[],
            cache=self.sync_cache
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

        reviewer.violation_definitions = {
            'page.title.size': {'default_value': 70},
        }

        validator = TitleValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.title_count': 1,
            'page.title': ['the title']
        }

        validator.validate()

        expect(validator.add_violation.called).to_be_false()

    def test_can_validate_empty_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html><title></title></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            value=page.url,
            points=50)

    def test_can_validate_no_title_tag(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            value=page.url,
            points=50)

    def test_can_validate_empty_html(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = ''

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': None
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.not_found',
            value=page.url,
            points=50)

    def test_can_validate_multiple_title(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            validators=[]
        )

        content = '<html><title>Ping</title><title>Pong</title></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        validator = TitleValidator(reviewer)

        validator.add_violation = Mock()
        validator.review.data = {
            'page.title_count': 2,
            'page.title': ['first', 'second']
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.multiple',
            value={'page_url': page.url, 'title_count': 2},
            points=50
        )

    def test_can_get_violation_definitions(self):
        reviewer = Mock()
        validator = TitleValidator(reviewer)

        definitions = validator.get_violation_definitions()

        expect(definitions).to_length(3)
        expect('page.title.not_found' in definitions).to_be_true()
        expect('page.title.multiple' in definitions).to_be_true()
        expect('page.title.size' in definitions).to_be_true()

    def test_can_validate_title_size(self):
        config = Config()
        config.MAX_TITLE_SIZE = 70

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[],
            cache=self.sync_cache
        )

        title = 'a' * 80
        content = '<html><title>%s</title></html>' % title

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        reviewer.violation_definitions = {
            'page.title.size': {'default_value': 70},
        }

        validator = TitleValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.title_count': 1,
            'page.title': title
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.size',
            value={'max_size': 70, 'page_url': page.url},
            points=10
        )

    def test_can_validate_title_size_with_domain(self):
        self.db.query(Key).delete()
        self.db.query(KeysCategory).delete()

        config = Config()
        config.MAX_TITLE_SIZE = 70

        key = Key(name='page.title.size')
        domain = DomainFactory.create(name='globo.com', url='http://globo.com')
        page = PageFactory.create(domain=domain, url='http://globo.com/a.html')

        self.sync_cache.redis.delete('violations-prefs-%s' % domain.name)

        DomainsViolationsPrefsFactory.create(
            domain=domain,
            key=key,
            value='10'
        )

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[],
            cache=self.sync_cache
        )

        title = 'a' * 80
        content = '<html><title>%s</title></html>' % title

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer.get_response = Mock(return_value=result)

        reviewer.violation_definitions = {
            'page.title.size': {'default_value': 70, 'key': key},
        }

        validator = TitleValidator(reviewer)
        validator.add_violation = Mock()
        validator.review.data = {
            'page.title_count': 1,
            'page.title': title
        }

        validator.validate()

        validator.add_violation.assert_called_once_with(
            key='page.title.size',
            value={'max_size': 10, 'page_url': page.url},
            points=10
        )

    def test_can_get_default_violations_values(self):
        config = Config()
        config.MAX_TITLE_SIZE = 70

        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=config,
            validators=[]
        )

        validator = TitleValidator(reviewer)

        violations_values = validator.get_default_violations_values(config)

        expect(violations_values).to_include('page.title.size')

        expect(violations_values['page.title.size']).to_length(2)

        expect(violations_values['page.title.size']).to_be_like({
            'value': config.MAX_TITLE_SIZE,
            'description': config.get_description('MAX_TITLE_SIZE')
        })
