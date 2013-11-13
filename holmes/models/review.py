#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

#from tornado.concurrent import return_future
#from motorengine import DESCENDING
#from motorengine import (
    #Document, ReferenceField, DateTimeField,
    #ListField, EmbeddedDocumentField, BooleanField,
    #UUIDField, StringField, IntField
#)
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base


class Review(Base):
    __tablename__ = "reviews"

    id = sa.Column(sa.Integer, primary_key=True)
    is_active = sa.Column('is_active', sa.Boolean, default=False, nullable=False)
    is_complete = sa.Column('is_complete', sa.Boolean, default=False, nullable=False)
    uuid = sa.Column('uuid', sa.String(36), default=uuid4, nullable=False)

    created_date = sa.Column('created_date', sa.DateTime, default=datetime.now, nullable=False)
    completed_date = sa.Column('completed_date', sa.DateTime, nullable=True)

    last_review_started_date = sa.Column('last_review_started_date', sa.DateTime, nullable=True)
    last_review_date = sa.Column('last_review_started_date', sa.DateTime, nullable=True)

    failure_message = sa.Column('failure_message', sa.String(2000), nullable=True)

    domain_id = sa.Column('domain_id', sa.Integer, sa.ForeignKey('domains.id'))
    page_id = sa.Column('page_id', sa.Integer, sa.ForeignKey('pages.id'))

    facts = relationship("Fact", backref="review")
    violations = relationship("Violation", backref="review")

    def to_dict(self):
        return {
            'page': self.page and self.page.to_dict() or None,
            'domain': self.domain and self.domain.name or None,
            'isComplete': self.is_complete,
            'uuid': str(self.uuid),
            'createdAt': self.created_date,
            'completedAt': self.completed_date,
            'facts': [fact.to_dict() for fact in self.facts],
            'violations': [violation.to_dict() for violation in self.violations]
        }

    def __str__(self):
        return str(self.uuid)

    def __repr__(self):
        return str(self)

    def add_fact(self, key, value, title, unit=None):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.fact import Fact  # to avoid circular dependency

        fact = Fact(key=key, value=value, title=title, unit=unit)

        self.facts.append(fact)

    def add_violation(self, key, title, description, points):
        if self.is_complete:
            raise ValueError("Can't add anything to a completed review.")

        from holmes.models.violation import Violation  # to avoid circular dependency

        violation = Violation(key=key, title=title, description=description, points=int(float(points)))

        self.violations.append(violation)

    @property
    def failed(self):
        return self.failure_message is not None

    @classmethod
    def get_last_reviews(cls, db, limit=12):
        return db.query(Review).filter(Review.is_active == True) \
                               .order_by(Review.completed_date.desc())[:limit]

    def get_violation_points(self):
        points = 0
        for violation in self.violations:
            points += violation.points
        return points

    @classmethod
    def by_uuid(cls, uuid, db):
        return db.query(Review).filter(Review.uuid == uuid).first()

    @property
    def violation_count(self):
        return len(self.violations)


#class Review(Document):
    #domain = ReferenceField('holmes.models.domain.Domain', required=True)
    #page = ReferenceField('holmes.models.page.Page', required=True)
    #facts = ListField(EmbeddedDocumentField('holmes.models.fact.Fact'))
    #violations = ListField(EmbeddedDocumentField('holmes.models.violation.Violation'))
    #violation_count = IntField(required=True, default=0, on_save=lambda doc, creating: len(doc.violations))

    #is_active = BooleanField(required=True, default=False)
    #is_complete = BooleanField(required=True, default=False)
    #uuid = UUIDField(default=uuid4)

    #created_date = DateTimeField(required=True, auto_now_on_insert=True)
    #completed_date = DateTimeField()
    #failure_message = StringField(required=False)

    #def add_fact(self, key, value, title, unit=None):
        #if self.is_complete:
            #raise ValueError("Can't add anything to a completed review.")

        #from holmes.models.fact import Fact  # to avoid circular dependency

        #fact = Fact(key=key, value=value, title=title, unit=unit)

        #self.facts.append(fact)

    #def add_violation(self, key, title, description, points):
        #if self.is_complete:
            #raise ValueError("Can't add anything to a completed review.")

        #from holmes.models.violation import Violation  # to avoid circular dependency

        #violation = Violation(key=key, title=title, description=description, points=int(float(points)))

        #self.violations.append(violation)

    #def to_dict(self):
        #return {
            #'page': self.page and self.page.to_dict() or None,
            #'domain': self.domain and self.domain.name or None,
            #'isComplete': self.is_complete,
            #'uuid': str(self.uuid),
            #'createdAt': self.created_date,
            #'completedAt': self.completed_date,
            #'facts': [fact.to_dict() for fact in self.facts],
            #'violations': [violation.to_dict() for violation in self.violations]
        #}

    #@property
    #def failed(self):
        #return self.failure_message is not None

    #def __str__(self):
        #return str(self.uuid)

    #def __repr__(self):
        #return str(self)

    #def get_violation_points(self):
        #points = 0
        #for violation in self.violations:
            #points += violation.points
        #return points

    #@classmethod
    #def handle_get_last_reviews(cls, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback([])
                #return

            #callback(arguments[0])

        #return handle

    #@classmethod
    #@return_future
    #def get_last_reviews(cls, limit=12, callback=None):
        #Review.objects \
            #.filter(is_active=True) \
            #.order_by(Review.completed_date, DESCENDING) \
            #.limit(limit) \
            #.find_all(callback=cls.handle_get_last_reviews(callback))
