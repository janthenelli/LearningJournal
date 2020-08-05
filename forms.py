from wtforms import Form, StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length, EqualTo, ValidationError
from wtforms.fields.html5 import IntegerField, DateField

from models import User, Entry


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('User with that email already exists.')

def title_exists(form, field):
    if User.select().where(User.email ** field.data).exists():
        raise ValidationError('That title has already been user, select a unique title.')

class RegistrationForm(Form):
    email = StringField(
        'Email',
        validators=[
            InputRequired(),
            Email(),
            email_exists
        ]
    )
    username = StringField(
        'Username',
        validators=[
            InputRequired()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Length(min=8),
            EqualTo('password2', message="Passwords must match.")
        ]
    )
    password2 = PasswordField(
        'Confirm Password',
        validators=[
            InputRequired()
        ]
    )

class LoginForm(Form):
    email = StringField(
        'Email',
        validators=[
            InputRequired(),
            Email()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            InputRequired()
        ]
    )

class EntryForm(Form):
    title = StringField(
        'Title',
        validators=[
            InputRequired(message="You must include a title for your entry.")
            title_exists
        ]
    )
    date = DateField(
        'Date',
        validators=[
            InputRequired(message="Please enter a date.")
        ]
    )
    time_spent = IntegerField(
        'Number of hours spent on task',
        validators=[
            InputRequired(message="How long did this task take you to complete?")
        ]
    )
    learned = TextAreaField(
        'What you learned',
        validators=[
            InputRequired(message="What did you learn?")
        ]
    )
    resources = TextAreaField(
        'Resources you need to remember'
    )