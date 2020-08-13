import datetime
import re

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


class MetaModel(Model):
    class Meta:
        database=DATABASE

class Entry(MetaModel):
    user = ForeignKeyField(
        User,
        related_name='entries'
    )
    title = CharField(unique=True)
    date = DateField(default=datetime.date.today)
    time_spent = IntegerField(default=0)
    learned = TextField()
    resources = TextField()


class Tag(MetaModel):
    tag = CharField()

class EntryTag(Model):
    entry = ForeignKeyField(Entry)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = DATABASE
        indexes = (
            (('entry', 'tags'), True),
        )

    @classmethod
    def tag_current_entries(cls, tag):
        try:
            entry_tags = Entry.select().where(Entry.learned.contains(tag.tag))
        except DoesNotExist:
            pass
        else:
            try:
                for entry in entry_tags:
                    cls.create(
                        entry=entry,
                        tag=tag
                    )
            except IntegrityError:
                pass

    @classmethod
    def tag_new_entry(cls, entry):
        try:
            entry_tags = Tag.select().where(Tag.tag.in_(re.findall(r"[\w']+|[.,!?;]", entry.learned)))
        except DoesNotExist:
            pass
        else:
            try:
                for tag in entry_tags:
                    cls.create(
                        entry=entry,
                        tag=tag
                    )
            except IntegrityError:
                pass

    @classmethod
    def remove_tag(cls, entry):
        try:
            entry_tags = Tag.select().where(Tag.tag.not_in(re.findall(r"[\w']+|{.,!?;]", entry.learned)))
        except DoesNotExist:
            pass
        else:
            try:
                for tag in entry_tags:
                    unwanted_tag = cls.get(tag=tag, entry=entry)
            except DoesNotExist:
                pass
            else:
                unwanted_tag.delete_instance()


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Tag, Entry, EntryTag], safe=True)
    DATABASE.close()