#!/usr/bin/python
# -*- coding: utf-8 -*-

import lxml.html
from mock import Mock

from holmes.config import Config
from holmes.reviewer import Reviewer
from holmes.validators.meta_tags import MetaTagsValidator
from tests.unit.base import ValidatorTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestMetaTagsValidator(ValidatorTestCase):

    def test_get_meta_tags(self):
        page = PageFactory.create()
        review = ReviewFactory.create(page=page)

        reviewer = Reviewer(
            api_url='http://localhost:2368',
            page_uuid=page.uuid,
            page_url=page.url,
            review_uuid=review.uuid,
            config=Config(),
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

        validator = MetaTagsValidator(reviewer)
        validator.add_fact = Mock()
        validator.validate()

        validator.add_fact.assert_called_once_with(
            key='meta.tags',
            unit='values',
            title='Meta Tags',
            value='[{"content":"utf-8","property":null,"key":"charset"},{"content":"text\\/html;charset=UTF-8","property":"http-equiv","key":"Content-Type"},{"content":"BKmmuVQac1JM6sKlj3IoXQvffyIRJvJfbicMouA2a88","property":"name","key":"google-site-verification"},{"content":"width=device-width, initial-scale=1.0, maximum-scale=1.0","property":"name","key":"viewport"},{"content":"globo.com - Absolutamente tudo sobre not\\u00edcias, esportes e entretenimento","property":"property","key":"og:title"},{"content":"website","property":"property","key":"og:type"},{"content":"http:\\/\\/www.globo.com\\/","property":"property","key":"og:url"},{"content":"http:\\/\\/s.glbimg.com\\/en\\/ho\\/static\\/globocom2012\\/img\\/gcom_marca_og.jpg","property":"property","key":"og:image"},{"content":"globo.com","property":"property","key":"og:site_name"},{"content":"S\\u00f3 na globo.com voc\\u00ea encontra tudo sobre o conte\\u00fado e marcas das Organiza\\u00e7\\u00f5es Globo. O melhor acervo de v\\u00eddeos online sobre entretenimento, esportes e jornalismo do Brasil.","property":"property","key":"og:description"},{"content":"224969370851736","property":"property","key":"fb:page_id"},{"content":"S\\u00f3 na globo.com voc\\u00ea encontra tudo sobre o conte\\u00fado e marcas das Organiza\\u00e7\\u00f5es Globo. O melhor acervo de v\\u00eddeos online sobre entretenimento, esportes e jornalismo do Brasil.","property":"name","key":"description"},{"content":"Not\\u00edcias, Entretenimento, Esporte, Tecnologia, Portal, Conte\\u00fado, Rede Globo, TV Globo, V\\u00eddeos, Televis\\u00e3o","property":"name","key":"keywords"},{"content":"Globo.com","property":"name","key":"application-name"},{"content":"#0669DE","property":"name","key":"msapplication-TileColor"},{"content":"http:\\/\\/s.glbimg.com\\/en\\/ho\\/static\\/globocom2012\\/img\\/globo-win-tile.png","property":"name","key":"msapplication-TileImage"}]')
