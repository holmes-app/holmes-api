#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import defaultdict
import sqlalchemy as sa
from sqlalchemy import func, distinct
from datetime import date, datetime, timedelta

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

    def to_dict(self):
        return {
            'domain_name': str(self.domain_name),
            'url': self.url,
            'effective_url': self.effective_url,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'completed_date': self.completed_date,
            'review_url': self.review_url
        }

    def __str__(self):
        return "%s (%s)" % (self.url, self.status_code)

    def __repr__(self):
        return str(self)

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

    @classmethod
    def get_last_requests(self, db, current_page=1, page_size=10,
                          domain_filter=None, status_code_filter=None):
        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        query = db.query(Request)

        if domain_filter:
            from holmes.models.domain import Domain
            domain = Domain.get_domain_by_name(domain_filter, db)
            if domain:
                query = query.filter(Request.domain_name == domain.name)

        if status_code_filter and int(status_code_filter):
            query = query.filter(Request.status_code == status_code_filter)

        return query.order_by('id desc')[lower_bound:upper_bound]

    @classmethod
    def get_requests_count_by_status(self, db, limit=1000):
        per_domains = {'_all': defaultdict(int)}

        from holmes.models.domain import Domain
        for domain in db.query(Domain).all():
            requests = db \
                .query(
                    Request.status_code,
                    sa.func.count(Request.id).label('count')
                ) \
                .filter(Request.domain_name == domain.name) \
                .group_by(Request.status_code) \
                .order_by('count DESC') \
                .limit(limit) \
                .all()
            per_domains[domain.name] = requests

            # calculating all domains by counting each domain
            for req in requests:
                per_domains['_all'][req[0]] += req[1]

        per_domains['_all'] = per_domains['_all'].items()

        return per_domains

    @classmethod
    def delete_old_requests(self, db, config, limit=1000):
        dt = date.today() - timedelta(days=config.DAYS_TO_KEEP_REQUESTS)

        older_requests = db \
            .query(Request) \
            .filter(Request.completed_date <= dt) \
            .limit(limit) \

        older_requests_ids = [item.id for item in older_requests]

        if not older_requests_ids:
            return None

        return db \
            .query(Request) \
            .filter(Request.id.in_(older_requests_ids)) \
            .delete(synchronize_session=False)

    @classmethod
    def get_all_status_code(self, db):
        status_code_list = db \
            .query(distinct(Request.status_code).label('status_code')) \
            .all()

        result = []

        for value in status_code_list:
            result.append({
                'statusCode': value.status_code,
                'statusCodeTitle': get_status_code_title(value.status_code)
          })

        return result
