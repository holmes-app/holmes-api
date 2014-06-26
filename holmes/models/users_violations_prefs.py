#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa

from holmes.models import Base


class UsersViolationsPrefs(Base):
    __tablename__ = "users_violations_prefs"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'))
    key_id = sa.Column('key_id', sa.Integer, sa.ForeignKey('keys.id'))
    is_active = sa.Column('is_active', sa.Boolean, default=True, nullable=False)

    def __str__(self):
        return '%s: %s' % (self.user.email, self.key.name)

    def __repr__(self):
        return str(self)

    def to_dict(self):
        return {
            'user': self.user.email,
            'key': self.key.name,
            'is_active': self.is_active
        }

    @classmethod
    def get_prefs(cls, db, user):
        prefs = db \
            .query(UsersViolationsPrefs) \
            .filter(UsersViolationsPrefs.user_id == user.id) \
            .all()

        result = {}
        for pref in prefs:
            result.update({pref.key.name: pref.is_active})
        return result

    @classmethod
    def update_by_user(cls, db, user, data):
        from holmes.models import Key

        if not user or not data:
            return

        for item in data:
            if 'key' not in item or 'is_active' not in item:
                continue

            key = Key.get_by_name(db, item.get('key'))
            if not key:
                continue

            is_active = item.get('is_active', True)

            db \
                .query(UsersViolationsPrefs) \
                .filter(
                    UsersViolationsPrefs.user_id == user.id,
                    UsersViolationsPrefs.key_id == key.id
                ) \
                .update(
                    {'is_active': is_active}
                )

        db.flush()

    @classmethod
    def delete_prefs(cls, db, user, items):
        from holmes.models import Key

        for key_name in items:
            key = Key.get_by_name(db, key_name)
            if not key:
                continue

            db \
                .query(UsersViolationsPrefs) \
                .filter(
                    UsersViolationsPrefs.key_id == key.id,
                    UsersViolationsPrefs.user_id == user.id
                ) \
                .delete()

        db.flush()

    @classmethod
    def insert_pref(cls, db, user, key, is_active):
        pref = UsersViolationsPrefs(user=user, key=key, is_active=is_active)
        db.add(pref)
        db.flush()

    @classmethod
    def insert_prefs(cls, db, user, items):
        from holmes.models import Key

        if not user:
            return

        data = []
        for key_name in items:
            key = Key.get_by_name(db, key_name)

            if not key:
                continue

            data.append({
                'user_id': user.id,
                'key_id': key.id,
                'is_active': True
            })

        db.execute(UsersViolationsPrefs.__table__.insert(), data)
