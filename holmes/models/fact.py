#!/usr/bin/python
# -*- coding: utf-8 -*-


#from motorengine import Document, StringField, JsonField
import sqlalchemy as sa

from holmes.models import Base


class Fact(Base):
    __tablename__ = "facts"

    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column('title', sa.String(2000), nullable=False)
    key = sa.Column('key', sa.String(2000), nullable=False)
    unit = sa.Column('unit', sa.String(2000), nullable=False)
    value = sa.Column('value', sa.String(4000), nullable=False)

    review_id = sa.Column('review_id', sa.Integer, sa.ForeignKey('reviews.id'))

    def to_dict(self):
        return {
            'title': self.title,
            'key': self.key,
            'unit': self.unit,
            'value': self.value
        }

    def __str__(self):
        unit = self.unit != 'value' and self.unit or ''
        value = self.value

        if unit in ['kb']:
            value = '%.2f' % float(value)

        return '%s: %s%s' % (self.key, value, unit)

    def __repr__(self):
        return str(self)

#class Fact(Document):
    #title = StringField(required=True)
    #key = StringField(required=True)
    #unit = StringField(required=True, default='value')
    #value = JsonField(required=True)

    #def to_dict(self):
        #return {
            #'title': self.title,
            #'key': self.key,
            #'unit': self.unit,
            #'value': self.value
        #}

    #def __str__(self):
        #unit = self.unit != 'value' and self.unit or ''
        #value = self.value

        #if unit in ['kb']:
            #value = '%.2f' % float(value)

        #return '%s: %s%s' % (self.key, value, unit)

    #def __repr__(self):
        #return str(self)
