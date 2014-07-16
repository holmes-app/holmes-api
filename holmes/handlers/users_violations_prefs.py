#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.gen import coroutine
from ujson import loads

from holmes.models import UsersViolationsPrefs
from holmes.handlers import BaseHandler


class UsersViolationsPrefsHandler(BaseHandler):

    @coroutine
    def get(self):
        user = self.get_authenticated_user()

        if not user:
            return

        user_prefs = UsersViolationsPrefs.get_prefs(self.db, user)

        violation_defs = self.application.violation_definitions

        user_prefs_keys = set(user_prefs.keys())
        violation_defs_keys = set(violation_defs.keys())

        insert_items = list(violation_defs_keys - user_prefs_keys)
        if insert_items:
            UsersViolationsPrefs.insert_prefs(self.db, user, insert_items)

        remove_items = list(user_prefs_keys - violation_defs_keys)
        if remove_items:
            UsersViolationsPrefs.delete_prefs(self.db, user, remove_items)

        result = []
        for key_name in violation_defs:
            category = violation_defs[key_name]['category']
            name = violation_defs[key_name]['title']
            description = violation_defs[key_name]['generic_description']
            is_active = user_prefs.get(key_name, True)

            result.append({
                'key': key_name,
                'name': self._(name),
                'description': self._(description),
                'category': self._(category),
                'is_active': is_active
            })

        self.write_json(result)

    @coroutine
    def post(self):
        user = self.get_authenticated_user()

        if not user:
            return

        post_data = loads(self.request.body)

        UsersViolationsPrefs.update_by_user(self.db, user, post_data)

        self.write_json({
            'reason': self._('Preferences successfully saved!'),
            'description': self._('Preferences successfully saved!')
        })
