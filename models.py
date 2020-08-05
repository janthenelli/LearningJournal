import datetime

from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *


DATABASE = SqliteDatabase('journal.db')


class User(UserMixin, Model):
    username = CharField()
    email = CharField(unique=True)
    password = CharField(max_length=100)

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, username, email, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    username=username,
                    email=email,
                    password=generate_password_hash(password)
                )
        except IntegrityError:
            raise ValueError("User already exists.")

class Entry(Model):
    user = ForeignKeyField(
        rel_model=User,
        related_name='entries'
    )
    title = CharField(unique=True)
    date = DateField(default=datetime.date.today)
    time_spent = IntegerField(default=0)
    learned = TextField()
    resources = TextFeild

    class Meta:
        database = DATABASE


