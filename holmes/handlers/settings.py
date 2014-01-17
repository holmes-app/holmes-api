#!/usr/bin/python
# -*- coding: utf-8 -*-

from holmes.models import Settings
from holmes.handlers import BaseHandler


class TaxHandler(BaseHandler):
    def post(self):
        tax = float(self.get_argument('tax'))

        self.db.query(Settings).update({'lambda_score': Settings.lambda_score + tax})

        self.write('OK')
        self.finish()
