#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock, call
from preggy import expect

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.facters.heading_hierarchy import HeadingHierarchyFacter
from tests.unit.base import FacterTestCase
from tests.fixtures import PageFactory


class TestHeadingHierarchyFacter(FacterTestCase):

    def test_can_get_facts(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
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
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = HeadingHierarchyFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(1)
        expect(facter.review.data).to_include('page.heading_hierarchy')

        expect(facter.add_fact.call_args_list).to_include(
            call(
                key='page.heading_hierarchy',
                value=[
                    ('h1', 'globo.com'),
                    ('h2', u'ANP: gigantes do petr\xf3leo desistem de leil\xe3o do pr\xe9-sal'),
                    ('h2', u'Pol\xedcia conclui que m\xe3e matou as filhas em SP'),
                    ('h2', u'Isolados por tempestade no M\xe9xico, 42 brasileiros recorrem \xe0 embaixada'),
                    ('h2', 'Show do Sorriso Maroto tem uma morte em tiroteio'),
                    ('h2', u'Casal \xe9 morto e crian\xe7as s\xe3o largadas em via'),
                    ('h2', 'AO VIVO: Almah e Hibria tocam no Rock in Rio'),
                    ('h2', u'SIGA AQUI: f\xe3 da banda Ghost faz homenagem'),
                    ('h2', "Thales pede e Nicole aparece em 'Amor'; veja"),
                    ('h2', u'Vasco e Tim\xe3o t\xeam puni\xe7\xe3o mudada'),
                    ('h2', u'Suposta bronca de Messi gera discuss\xe3o; veja'),
                    ('h3', 'rock in rio'),
                    ('h2', u'not\xedcias'),
                    ('h2', 'esportes'),
                    ('h2', 'entretenimento'),
                    ('h2', 'tecnologia&games'),
                    ('h2', 'moda&beleza'),
                    ('h3', u'semana de moda de mil\xe3o'),
                    ('h3', u'com delineador, sombra e l\xe1pis'),
                    ('h3', 'tudo igual'),
                    ('h3', u'veja tamb\xe9m'),
                    ('h3', 'GNT'),
                    ('h3', 'vogue'),
                    ('h2', u'CASA&DECORA\xc7\xc3O'),
                    ('h3', 'da madeira ao cristal'),
                    ('h3', 'para comer com os olhos'),
                    ('h3', 'Gosta de cor nos ambientes'),
                    ('h3', u'veja tamb\xe9m'),
                    ('h3', 'CASA E JARDIM'),
                    ('h3', 'CASA VOGUE'),
                    ('h2', 'FAMOSOSFAMOSOS'),
                    ('h3', 'ego'),
                    ('h3', 'quem'),
                    ('h2', u'novelas, s\xe9ries, programas e muito maisnovelas, s\xe9ries, programas e muito mais'),
                    ('h3', 'ESTILO TV'),
                    ('h3', 'SARAMANDAIA'),
                    ('h3', u'AMOR \xc0 VIDA'),
                    ('h3', 'SANGUE BOM'),
                    ('h3', 'JOIA RARA'),
                    ('h2', u'M\xfasica'),
                    ('h3', u'm\xfasica.com.br'),
                    ('h3', u'g1 m\xfasica'),
                    ('h3', 'multishow'),
                    ('h3', 'globoradio'),
                    ('h3', 'TOP 3 LETRAS'),
                    ('h4', ''),
                    ('h4', ''),
                    ('h4', ''),
                    ('h3', u'ENCONTRE LETRAS E TRADU\xc7\xd5ES'),
                    ('h3', u'top globot\xe1 todo mundo clicando...'),
                    ('h1', 'globo.tv'),
                    ('h2', u'servi\xe7os')
                ]))

    def test_empty_content(self):
        page = PageFactory.create()

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            page_score=0.0,
            config=Config(),
            facters=[]
        )

        content = '<html></html>'

        result = {
            'url': page.url,
            'status': 200,
            'content': content,
            'html': lxml.html.fromstring(content)
        }
        reviewer.responses[page.url] = result
        reviewer._wait_for_async_requests = Mock()
        reviewer.save_review = Mock()
        response = Mock(status_code=200, text=content, headers={})
        reviewer.content_loaded(page.url, response)

        facter = HeadingHierarchyFacter(reviewer)
        facter.add_fact = Mock()

        facter.async_get = Mock()
        facter.get_facts()

        expect(facter.review.data).to_length(1)
        expect(facter.review.data).to_be_like({'page.heading_hierarchy': []})
        expect(facter.add_fact.called).to_be_false()

    def test_can_get_fact_definitions(self):
        reviewer = Mock()
        facter = HeadingHierarchyFacter(reviewer)
        definitions = facter.get_fact_definitions()

        expect(definitions).to_length(1)
        expect('page.heading_hierarchy' in definitions).to_be_true()
