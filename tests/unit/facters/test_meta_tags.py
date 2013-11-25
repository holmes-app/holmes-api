#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.meta_tags import MetaTagsFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestMetaTagsFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            config=Config(),
            facters=[]
        )

        content = self.get_file('globo.html')

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content)
        reviewer.content_loaded(page.url, response)

        facter = MetaTagsFacter(reviewer)
        facter.add_fact = Mock()

        facter.get_facts()

        values = [{'content': 'utf-8', 'property': None, 'key': 'charset'},
                  {'content': 'text/html;charset=UTF-8', 'property': 'http-equiv', 'key': 'Content-Type'},
                  {'content': 'BKmmuVQac1JM6sKlj3IoXQvffyIRJvJfbicMouA2a88', 'property': 'name', 'key': 'google-site-verification'},
                  {'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.0', 'property': 'name', 'key': 'viewport'},
                  {'content': u'globo.com - Absolutamente tudo sobre not\xedcias, esportes e entretenimento', 'property': 'property', 'key': 'og:title'},
                  {'content': 'website', 'property': 'property', 'key': 'og:type'},
                  {'content': 'http://www.globo.com/', 'property': 'property', 'key': 'og:url'},
                  {'content': 'http://s.glbimg.com/en/ho/static/globocom2012/img/gcom_marca_og.jpg', 'property': 'property', 'key': 'og:image'},
                  {'content': 'globo.com', 'property': 'property', 'key': 'og:site_name'},
                  {'content': u'S\xf3 na globo.com voc\xea encontra tudo sobre o conte\xfado e marcas das Organiza\xe7\xf5es Globo. O melhor acervo de v\xeddeos online sobre entretenimento, esportes e jornalismo do Brasil.', 'property': 'property', 'key': 'og:description'},
                  {'content': '224969370851736', 'property': 'property', 'key': 'fb:page_id'},
                  {'content': u'S\xf3 na globo.com voc\xea encontra tudo sobre o conte\xfado e marcas das Organiza\xe7\xf5es Globo. O melhor acervo de v\xeddeos online sobre entretenimento, esportes e jornalismo do Brasil.', 'property': 'name', 'key': 'description'},
                  {'content': u'Not\xedcias, Entretenimento, Esporte, Tecnologia, Portal, Conte\xfado, Rede Globo, TV Globo, V\xeddeos, Televis\xe3o', 'property': 'name', 'key': 'keywords'},
                  {'content': 'Globo.com', 'property': 'name', 'key': 'application-name'},
                  {'content': '#0669DE', 'property': 'name', 'key': 'msapplication-TileColor'},
                  {'content': 'http://s.glbimg.com/en/ho/static/globocom2012/img/globo-win-tile.png', 'property': 'name', 'key': 'msapplication-TileImage'}]

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='meta.tags',
                value=values,
                unit='values',
                title='Meta Tags'
            ))

        expect(facter.review.data).to_include('meta.tags')
        expect(facter.review.data).to_be_like({'meta.tags': values})
