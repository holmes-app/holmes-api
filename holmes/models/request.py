#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy import func

from holmes.utils import get_status_code_title
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

    @classmethod
    def get_status_code_info(self, domain_name, db):
        result = []

        query = db \
            .query(
                Request.status_code,
                sa.func.count(Request.status_code).label('total')
            ) \
            .filter(Request.domain_name == domain_name) \
            .group_by(Request.status_code) \
            .all()

        for i in query:
            result.append({
                'code': i.status_code,
                'title': get_status_code_title(i.status_code),
                'total': i.total
            })

        return result

    @classmethod
    def get_requests_by_status_code(self, domain_name, status_code, db, current_page=1, page_size=10):
        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        requests = db \
            .query(Request.id, Request.url, Request.review_url, Request.completed_date) \
            .filter(Request.domain_name == domain_name) \
            .filter(Request.status_code == status_code) \
            .order_by('completed_date desc')[lower_bound:upper_bound]

        return requests

    @classmethod
    def get_requests_by_status_count(self, domain_name, status_code, db):
        return db \
            .query(func.count(Request.id)) \
            .filter(Request.domain_name == domain_name) \
            .filter(Request.status_code == status_code) \
            .scalar()
