#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base


class Key(Base):
    __tablename__ = "keys"

    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column('key', sa.String(2000), nullable=False)

    facts = relationship("Fact", cascade="all,delete", backref="key")
    violations = relationship("Violation", cascade="all,delete", backref="key")

    def __str__(self):
        return '%s' % (self.key)

    def __repr__(self):
        return str(self)
