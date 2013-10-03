#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4

from motorengine import (
    Document, ReferenceField, DateTimeField,
    ListField, EmbeddedDocumentField, BooleanField,
    UUIDField
)


class Review(Document):
    page = ReferenceField("holmes.models.page.Page", required=True)
    facts = ListField(EmbeddedDocumentField("holmes.models.fact.Fact"))
    violations = ListField(EmbeddedDocumentField("holmes.models.violation.Violation"))

    is_complete = BooleanField(required=True, default=False)
    uuid = UUIDField(default=uuid4)

    created_date = DateTimeField(required=True, auto_now_on_insert=True)
    completed_date = DateTimeField()

    def add_fact(self, key, value, unit=None):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.fact import Fact  # to avoid circular dependency

        fact = Fact(key=key, value=value, unit=unit)

        self.facts.append(fact)

    def add_violation(self, key, title, description, points):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.violation import Violation  # to avoid circular dependency

        violation = Violation(key=key, title=title, description=description, points=points)

        self.violations.append(violation)

    def to_dict(self):
        return {
            "page": self.page and self.page.to_dict() or None,
            "domain": self.page and self.page.domain.name or None,
            "isComplete": self.is_complete,
            "uuid": str(self.uuid),
            "createdAt": self.created_date,
            "completedAt": self.completed_date,
            "facts": [fact.to_dict() for fact in self.facts],
            "violations": [violation.to_dict() for violation in self.violations]
        }

    def __str__(self):
        return str(self.uuid)

    def __repr__(self):
        return str(self)
