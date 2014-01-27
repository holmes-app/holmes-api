#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base


class Request(Base):
    __tablename__ = "requests"

    id = sa.Column(sa.Integer, primary_key=True)
    domain_name = sa.Column('domain_name', sa.String(120), nullable=False)
    url = sa.Column('url', sa.Text(), nullable=False)
    effective_url = sa.Column('effective_url', sa.Text(), nullable=False)
    status_code = sa.Column('status_code', sa.Integer, nullable=False)
    response_time = sa.Column('response_time', sa.Float, nullable=False)
    completed_date = sa.Column('completed_date', sa.Date, nullable=False)
    review_url = sa.Column('review_url', sa.Text(), nullable=False)
