#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.facters import Facter


class HeadingHierarchyFacter(Facter):
    @classmethod
    def get_fact_definitions(cls):
        return {
            'page.heading_hierarchy': {
                'title': 'Heading Hierarchy',
                'description': lambda value: list(value),
                'unit': 'heading-hierarchy',
                'category': 'SEO',
            },
        }

    def get_facts(self):
        elements = self.get_heading()

        self.review.data['page.heading_hierarchy'] = []

        for element in elements:
            data = (element.tag, element.text_content().strip())
            self.review.data['page.heading_hierarchy'].append(data)

        if self.review.data['page.heading_hierarchy']:
            self.add_fact(
                key='page.heading_hierarchy',
                value=self.review.data['page.heading_hierarchy']
            )

    def get_heading(self):
        return self.reviewer.current_html.cssselect('body h1,h2,h3,h4,h5,h6')
