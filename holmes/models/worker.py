#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime

import sqlalchemy as sa

from holmes.models import Base
from holmes.utils import get_domain_from_url


class Worker(Base):
    __tablename__ = "workers"

    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column('uuid', sa.String(36), default=uuid4, nullable=False)
    last_ping = sa.Column('last_ping', sa.DateTime, default=datetime.utcnow, nullable=False)

    current_url = sa.Column('current_url', sa.Text)

    def __str__(self):
        return 'Worker %s' % str(self.uuid)

    def __repr__(self):
        return str(self)

    @property
    def working(self):
        return self.current_url is not None

    def to_dict(self):
        domain, domain_url = get_domain_from_url(self.current_url)
        return {
            'uuid': str(self.uuid),
            'last_ping': self.last_ping,
            'current_url': self.current_url,
            'working': self.working,
            'domain_name': domain
        }

    @classmethod
    def by_uuid(cls, uuid, db):
        return db.query(Worker).filter(Worker.uuid == uuid).first()
