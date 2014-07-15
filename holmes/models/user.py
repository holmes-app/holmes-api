#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from holmes.models import Base


class User(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    fullname = sa.Column('fullname', sa.String(200), nullable=False)
    email = sa.Column('email', sa.String(100), nullable=False, unique=True)
    provider = sa.Column('provider', sa.String(10), nullable=True)
    is_superuser = sa.Column(
        'is_superuser',
        sa.Boolean,
        nullable=False,
        default=False
    )
    last_login = sa.Column('last_login', sa.DateTime, nullable=True)
    locale = sa.Column('locale', sa.String(10), nullable=True)

    violations_prefs = relationship('UsersViolationsPrefs', backref='user')

    def to_dict(self):
        return {
            'fullname': self.fullname,
            'email': self.email,
            'is_superuser': bool(self.is_superuser),
            'last_login': self.last_login,
            'locale': self.locale,
        }

    def __str__(self):
        return str(self.email)

    def __repr__(self):
        return str(self)

    @classmethod
    def by_email(cls, email, db):
        return db.query(User).filter(User.email == email).first()

    @classmethod
    def add_user(cls, db, fullname, email, provider, last_login=None):
        user = User(fullname=fullname, email=email,
                    provider=provider, last_login=last_login)
        db.add(user)
        db.flush()
        return user

    @classmethod
    def update_locale(cls, db, user, locale):
        db \
            .query(User).filter(User.id == user.id) \
            .update({'locale': locale})
