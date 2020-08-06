from flask import Flask, render_template, flash, g, redirect, url_for, request
from flask_bcrypt import check_password_hash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from peewee import DoesNotExist

import forms
import models

DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

app = Flask(__name__)
app.secret_key = 'ailsdufalidhf9384029fbwdnfmsdff9238r'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None
    
    
@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user
    
    
@app.after_request
def after_request():
    g.db.close()
    return response

@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        try:
            models.User.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
        except ValueError:
            flash("User with '{}' email already exists.".format(form.email.data), "error")
        else:
            flash("User '{}' created successfully!".format(form.email.data), "success")
            return redirect(url_for('index'))
    return render_template('register.html' form=form)

@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except DoesNotExist:
            flash("Email or password does not match.", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Welcome, {}!".format(user.username), "success")
                return redirect(url_for('index'))
            else:
                flash("Email or password does not match.", "error")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/')
@app.route('/entries')
def index():
    entries = models.Entry.select()
    display_entries = []
    for entry in entries:
        entry_tag = set((models.Tags.select().join(models.EntryTag).where(models.EntryTag.entry == entry)))
        display_entries.append([entry, entry_tag])
    return render_template('index.html', entries=display_entries)

@app.route('/new', methods=('GET', 'POST'))
@login_required
def new_entry():
    form = forms.EntryForm()
    if form.validate_on_submit():
        models.Entry.create(
            user = g.user._get_current_object(),
            title = form.title.data.strip(),
            date = form.date.data,
            time_spent = form.time_spent.data,
            learned = form.learned.data.strip(),
            resources = form.resources.data.strip()
        )
        flash("Entry created!", "success")
        return redirect(url_for('index'))
    return render_template('new.html')

