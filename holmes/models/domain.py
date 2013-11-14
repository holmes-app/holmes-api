#!/usr/bin/python
# -*- coding: utf-8 -*-

#from tornado.concurrent import return_future
#from motorengine import Document, URLField, StringField, DESCENDING

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base
#from holmes.models.review import Review


class Domain(Base):
    __tablename__ = "domains"

    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column('url', sa.String(2000), nullable=False)
    url_hash = sa.Column('url_hash', sa.String(128), nullable=False)
    name = sa.Column('name', sa.String(2000), nullable=False)

    pages = relationship("Page", backref="domain")
    reviews = relationship("Review", backref="domain")

    def to_dict(self):
        return {
            "url": self.url,
            "name": self.name
        }

    @classmethod
    def get_pages_per_domain(cls, db):
        from holmes.models import Page
        return dict(db.query(Page.domain_id, sa.func.count(Page.id)).group_by(Page.domain_id).all())

    def get_page_count(self, db):
        from holmes.models import Page
        return db.query(Page).filter(Page.domain_id == self.id).count()

    @classmethod
    def get_violations_per_domain(cls, db):
        from holmes.models import Review, Violation

        violations = db \
            .query(Review.domain_id, sa.func.count(Violation.id).label('count')) \
            .filter(Violation.review_id == Review.id) \
            .filter(Review.is_active == True) \
            .group_by(Review.domain_id) \
            .all()

        domains = {}
        for domain in violations:
            domains[domain.domain_id] = domain.count

        return domains

    def get_violation_data(self, db):
        from holmes.models import Review, Violation

        result = db.query(sa.func.count(Violation.id).label('count'), sa.func.sum(Violation.points).label('points')) \
            .join(Review, Violation.review_id == Review.id) \
            .filter(Review.domain_id == self.id) \
            .one()

        return (
            result.count, result.points
        )

    def get_violations_per_day(self, db):
        from holmes.models import Review, Violation  # Prevent circular dependency

        violations = db \
            .query(
                sa.func.year(Review.completed_date).label('year'),
                sa.func.month(Review.completed_date).label('month'),
                sa.func.day(Review.completed_date).label('day'),
                sa.func.count(Violation.id).label('violation_count'),
                sa.func.sum(Violation.points).label('violation_points')
            ).join(
                Domain, Domain.id == Review.domain_id
            ).join(
                Violation, Violation.review_id == Review.id
            ).filter(Review.is_complete == True).filter(Review.domain_id == self.id) \
            .group_by(
                sa.func.year(Review.completed_date),
                sa.func.month(Review.completed_date),
                sa.func.day(Review.completed_date),
            ) \
            .all()

        result = {}

        for day in violations:
            dt = "%d-%d-%d" % (day.year, day.month, day.day)
            result[dt] = {
                "violation_count": int(day.violation_count),
                "violation_points": int(day.violation_points)
            }

        return result

    def get_active_reviews(self, db, current_page=1, page_size=10):
        from holmes.models import Review, Violation  # Prevent circular dependency

        lower_bound = (current_page - 1) * page_size
        upper_bound = lower_bound + page_size

        items = db \
            .query(Review, sa.func.count(Violation.id).label('violation_count')) \
            .outerjoin(Violation, Violation.review_id == Review.id) \
            .filter(Review.is_active == True) \
            .filter(Review.domain == self) \
            .group_by(Review.id) \
            .order_by('violation_count desc')[lower_bound:upper_bound]

        return [item[0] for item in items]

    @classmethod
    def get_domain_by_name(self, domain_name, db):
        return db.query(Domain).filter(Domain.name == domain_name).first()

    def get_active_review_count(self, db):
        from holmes.models import Review

        return db.query(Review).filter(Review.is_active == True, Review.domain == self).count()


#class Domain(Document):
    #url = URLField(required=True)
    #name = StringField(required=True)

    #def to_dict(self):
        #return {
            #"url": self.url,
            #"name": self.name
        #}

    #@classmethod
    #def handle_get_violations_per_domain(cls, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #domains = {}
            #for domain in arguments[0]:
                #domains[domain['domain']] = domain['count']
            #callback(domains)

        #return handle

    #@classmethod
    #@return_future
    #def get_violations_per_domain(cls, callback=None):
        #Review.objects.aggregate.raw([
            #{"$match": {"is_active": True}},
            #{"$unwind": "$violations"},
            #{"$group": {"_id": {"domain": "$domain"}, "count": {"$sum": 1}}}
        #]).fetch(callback=cls.handle_get_violations_per_domain(callback))

    #@classmethod
    #def handle_get_pages_per_domain(cls, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #domains = {}
            #for domain in arguments[0]:
                #domains[domain['_id']] = domain['count']
            #callback(domains)

        #return handle

    #@classmethod
    #@return_future
    #def get_pages_per_domain(cls, callback=None):
        #Page.objects.aggregate.raw([
            #{"$group": {"_id": "$domain", "count": {"$sum": 1}}}
        #]).fetch(callback=cls.handle_get_pages_per_domain(callback))

    #def handle_get_page_count(self, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback(0)

            #callback(arguments[0][0]['count'])

        #return handle

    #@return_future
    #def get_page_count(self, callback=None):
        #Page.objects.aggregate.raw([
            #{"$match": {"domain": self._id}},
            #{"$group": {"_id": "$domain", "count": {"$sum": 1}}}
        #]).fetch(callback=self.handle_get_page_count(callback))

    #def handle_get_violation_data(self, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback((0, 0))
                #return

            #callback((arguments[0][0]['count'], arguments[0][0]['points']))

        #return handle

    #@return_future
    #def get_violation_data(self, callback=None):
        #Review.objects.aggregate.raw([
            #{"$match": {"domain": self._id, "is_active": True}},
            #{"$unwind": "$violations"},
            #{"$group": {"_id": "$domain", "count": {"$sum": 1}, "points": {"$sum": "$violations.points"}}}
        #]).fetch(callback=self.handle_get_violation_data(callback))

    #def handle_get_violations_per_day(self, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback([])
                #return

            #result = {}

            #for day in arguments[0]:
                #dt = "%d-%d-%d" % (day['year'], day['month'], day['day'])
                #result[dt] = {
                    #"violation_count": day['count'],
                    #"violation_points": day['points']
                #}

            #callback(result)

        #return handle

    #@return_future
    #def get_violations_per_day(self, callback=None):
        #Review.objects.aggregate.raw([
            #{"$match": {"domain": self._id, "is_complete": True}},
            #{"$project": {
                #"domain": 1,
                #"violations": 1,
                #"year": {"$year": "$completed_date"},
                #"month": {"$month": "$completed_date"},
                #"day": {"$dayOfMonth": "$completed_date"},
            #}},
            #{"$unwind": "$violations"},
            #{
                #"$group": {
                    #"_id": {
                        #"domain": "$domain", "year": "$year", "month": "$month", "day": "$day"
                    #},
                    #"count": {"$sum": 1},
                    #"points": {"$sum": "$violations.points"}
                #}
            #}
        #]).fetch(callback=self.handle_get_violations_per_day(callback))

    #def handle_get_active_reviews(self, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback([])
                #return

            #callback(arguments[0])

        #return handle

    #@return_future
    #def get_active_reviews(self, current_page=1, page_size=10, callback=None):
        #skip = (current_page - 1) * page_size
        #Review.objects \
              #.filter(is_active=True, domain=self) \
              #.order_by(Review.violation_count, DESCENDING) \
              #.skip(skip) \
              #.limit(page_size) \
              #.find_all(lazy=False, callback=self.handle_get_active_reviews(callback))

    #def handle_get_active_review_count(self, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #callback(0)
                #return

            #callback(arguments[0])

        #return handle

    #@return_future
    #def get_active_review_count(self, callback=None):
        #Review.objects.filter(is_active=True, domain=self).count(callback=self.handle_get_active_review_count(callback))

    #@classmethod
    #def handle_get_domain_by_name(self, domain_name, callback):
        #def handle(*arguments, **kwargs):
            #if len(arguments) > 1 and arguments[1]:
                #raise arguments[1]

            #if not arguments[0]:
                #from tornado import web
                #raise web.HTTPError(404, reason='Domain with name "%s" was not found!' % domain_name)

            #callback(arguments[0])

        #return handle

    #@classmethod
    #@return_future
    #def get_domain_by_name(self, domain_name, callback=None):
        #Domain.objects.get(name=domain_name, callback=self.handle_get_domain_by_name(domain_name, callback))
