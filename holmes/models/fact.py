#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, StringField, JsonField


class Fact(Document):
    title = StringField(required=True)
    key = StringField(required=True)
    unit = StringField(required=True, default='value')
    value = JsonField(required=True)

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
