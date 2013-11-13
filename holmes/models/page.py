#!/usr/bin/python
# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime
#from tornado.concurrent import return_future

#from motorengine import Document, URLField, StringField, ReferenceField, DateTimeField, UUIDField
import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base
#from holmes.models.review import Review


class Page(Base):
    __tablename__ = "pages"

    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column('url', sa.String(2000), nullable=False)
    uuid = sa.Column('uuid', sa.String(36), default=uuid4, nullable=False)
    created_date = sa.Column('created_date', sa.DateTime, default=datetime.now, nullable=False)

    last_review_started_date = sa.Column('last_review_started_date', sa.DateTime, nullable=True)
    last_review_date = sa.Column('last_review_started_date', sa.DateTime, nullable=True)

    domain_id = sa.Column('domain_id', sa.Integer, sa.ForeignKey('domains.id'))

    reviews = relationship("Review", backref="page")

    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'url': self.url
        }

    def __str__(self):
        return str(self.uuid)

    def __repr__(self):
        return str(self)



#class Page(Document):
    #uuid = UUIDField(default=uuid4)
    #title = StringField(required=False)
    #url = URLField(required=True)
    #origin = ReferenceField('holmes.models.domain.Page', required=False)
    #added_date = DateTimeField(required=True, auto_now_on_insert=True)
    #updated_date = DateTimeField(required=True, auto_now_on_insert=True, auto_now_on_update=True)

    #domain = ReferenceField('holmes.models.domain.Domain', required=True)
    ##last_review = ReferenceField('holmes.models.review.Review', required=False)
    #last_review_started_date = DateTimeField(required=False)
    #last_review_date = DateTimeField(required=False)

    #def to_dict(self):
        #return {
            #'uuid': str(self.uuid),
            #'title': self.title,
            #'url': self.url
        #}

    #def __str__(self):
        #return str(self.uuid)

    #def __repr__(self):
        #return str(self)

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
            #{"$match": {"page": self._id, "is_complete": True}},
            #{"$project": {
                #"page": 1,
                #"violations": 1,
                #"year": {"$year": "$completed_date"},
                #"month": {"$month": "$completed_date"},
                #"day": {"$dayOfMonth": "$completed_date"},
            #}},
            #{"$unwind": "$violations"},
            #{
                #"$group": {
                    #"_id": {
                        #"page": "$page", "year": "$year", "month": "$month", "day": "$day"
                    #},
                    #"count": {"$sum": 1},
                    #"points": {"$sum": "$violations.points"}
                #}
            #}
        #]).fetch(callback=self.handle_get_violations_per_day(callback))
