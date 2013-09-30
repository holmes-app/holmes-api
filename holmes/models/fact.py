#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, StringField, JsonField


class Fact(Document):
    key = StringField(required=True)
    unit = StringField(required=True, default="value")
    value = JsonField(required=True)

    def to_dict(self):
        return {
            "key": self.key,
            "unit": self.unit,
            "value": self.value
        }
