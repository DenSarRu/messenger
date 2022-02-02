"""Модуль с моделями таблиц для БД"""

import datetime

from sqlalchemy import Column, Table, String, Integer, Boolean, ForeignKey, \
    DateTime, Text
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

"""Таблица контактов."""
contact_table = Table('contact', Base.metadata,
                      Column('user_id', Integer, ForeignKey('user.id')),
                      Column('contact_id', Integer, ForeignKey('user.id')))


class User(Base):
    """
    Класс - таблица пользователей.
    """
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    pubkey = Column(Text)
    # password = Column(String)
    last_login = Column(DateTime)
    is_online = Column(Boolean)
    history = relationship('History', back_populates='user')
    contacts = relationship(
        'User',
        secondary=contact_table,
        backref='owner',
        primaryjoin=id == contact_table.c.user_id,
        secondaryjoin=id == contact_table.c.contact_id,
    )

    def __init__(self, name='Guest'):
        self.name = name
        self.pubkey = None

    def __repr__(self):
        return f'<Клиент: {self.name}>'


class History(Base):
    """
    Класс - таблица истории пользователей.
    """
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    time = Column(DateTime)
    ip = Column(String)
    user = relationship('User', back_populates='history')

    def __init__(self, user, ip):
        self.ip = ip
        self.user = user
        self.time = datetime.datetime.now()

    def __repr__(self):
        return f'<История {self.user.name}, {self.time}, {self.ip}>'


if __name__ == '__main__':
    user_name = input('Enter username: ')
    if len(user_name) == 0:
        new_user = User()
    else:
        new_user = User(user_name)
    print(new_user)
