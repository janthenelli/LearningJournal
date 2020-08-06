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
        rel_model=User,
        related_name='entries'
    )
    title = CharField(unique=True)
    date = DateField(default=datetime.date.today)
    time_spent = IntegerField(default=0)
    learned = TextField()
    resources = TextFeild


class Tag(MetaModel):
    tag = CharField()

class EntryTag(Model):
    entry = ForeignKeyField(Entry)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = DATABASE
        indexes = (
            (('entry', 'tags'), True)
        )

    @classmethod
    def tag_current_entries(cls, tag):
        try:
            entry_tags = Entry.select().where(Entry.content.contains(tag.tag))
        except DoesNotExist:
            pass
        else:
            try:
                or tag in entry_tags:
                cls.create(
                    entry=entry,
                    tag=tag
                )
            except IntegrityError:
                pass

    @classmethod
    def add_tag_to_new_entry(cls, entry):
        try:
            entry_tags = Tag.select().where(Tag.tag.in_(re.findall(r"[\w']+|[.,!?;]", every.content)))
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
            entry_tags = Tag.select().where(Tag.tag.not_in_(re.findall(r"[\w']+|{.,!?;]", every.content)))
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
    DATABASE.create_tables([User, Entry, Tag, EntryTag], safe=True)
    DATABASE.close()