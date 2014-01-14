#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base


class Settings(Base):
    __tablename__ = "settings"

    id = sa.Column(sa.Integer, primary_key=True)
    lambda_score = sa.Column(sa.Float, default=0.0)

    @classmethod
    def instance(cls, db):
        return db.query(Settings).first()
