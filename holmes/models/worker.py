#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

#from motorengine import Document, UUIDField, DateTimeField, ReferenceField
import sqlalchemy as sa
#from sqlalchemy.orm import relationship

from holmes.models import Base


class Worker(Base):
    __tablename__ = "workers"

    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column('uuid', sa.String(36), default=uuid4, nullable=False)
    last_ping = sa.Column('last_ping', sa.DateTime, default=datetime.now, nullable=False)

    current_url = sa.Column('current_url', sa.Text)
    #current_review_id = sa.Column('current_review_id', sa.Integer, sa.ForeignKey('reviews.id'))
    #current_review = relationship('Review')

    def __str__(self):
        return 'Worker %s' % str(self.uuid)

    def __repr__(self):
        return str(self)

    @property
    def working(self):
        return self.current_url is not None

    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'last_ping': str(self.last_ping),
            'current_url': self.current_url,
            'working': self.working
        }

    @classmethod
    def by_uuid(cls, uuid, db):
        return db.query(Worker).filter(Worker.uuid == uuid).first()
