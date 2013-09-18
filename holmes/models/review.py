#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import (
    Document, ReferenceField, DateTimeField,
    ListField, EmbeddedDocumentField, BooleanField
)


class Review(Document):
    page = ReferenceField("holmes.models.page.Page", required=True)
    facts = ListField(EmbeddedDocumentField("holmes.models.fact.Fact"))
    violations = ListField(EmbeddedDocumentField("holmes.models.violation.Violation"))

    is_complete = BooleanField(required=True, default=False)

    created_date = DateTimeField(required=True, auto_now_on_insert=True)

    def add_fact(self, key, value, unit=None):
        from holmes.models.fact import Fact  # to avoid circular dependency

        fact = Fact(key=key, value=value, unit=unit)

        self.facts.append(fact)

    def add_violation(self, key, title, description, points):
        from holmes.models.violation import Violation  # to avoid circular dependency

        violation = Violation(key=key, title=title, description=description, points=points)

        self.violations.append(violation)
