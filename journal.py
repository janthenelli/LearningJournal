from flask import Flask, render_template, flash, g, redirect, url_for, request, abort
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
def after_request(response):
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
    return render_template('register.html', form=form)

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
        entry_tag = set((models.Tag.select().join(models.EntryTag).where(models.EntryTag.entry == entry)))
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
        models.EntryTag.tag_new_entry(models.Entry.get(title=form.title.data.strip()))
        return redirect(url_for('index'))
    return render_template('new.html', form=form)

@app.route('/entries/<int:id>')
@login_required
def view_entry(id):
    try:
        selected_entry = models.Entry.get(models.Entry.id == id)
    except DoesNotExist:
        abort(404)
    else:
        selected_entry_tags = set((models.Tag.select().join(models.EntryTag).where(models.EntryTag.entry == selected_entry)))
    return render_template('detail.html', entry=selected_entry, tags=selected_entry_tags)

@app.route('/entries/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit_entry(id):
    try:
        entry = models.Entry.get(models.Entry.id == id)
    except models.DoesNotExist:
        abort(404)
    else:
        form = forms.EditForm(
            title=entry.title,
            date=entry.date,
            time_spent=entry.time_spent,
            learned=entry.learned,
            resources=entry.resources
        )
        if form.validate_on_submit():
            entry.title = form.title.data.strip()
            entry.date = form.date.data
            entry.time_spent = form.time_spent.data
            entry.learned = form.learned.data.strip()
            entry.resources = form.resources.data.strip()
            entry.save()
            flash("Entry updated.", "success")
            models.EntryTag.remove_tag(models.Entry.get(title=form.title.data.strip()))
            models.EntryTag.tag_new_entry(models.Entry.get(title=form.title.data.strip()))
            return redirect(url_for('index'))
    return render_template('edit.html', form=form, entry=entry)

@app.route('/entries/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete_entry(id):
    try:
        entry = models.Entry.get(models.Entry.id == id)
        try:
            tag_relationship = models.EntryTag.get(entry=entry)
            tag_relationship.delete_instance()
        except models.DoesNotExist:
            pass
    except models.DoesNotExist:
        abort(404)
    else:
        entry.delete_instance()
        flash("Entry deleted.", "success")
        return redirect(url_for('index'))

@app.route('/new_tag', methods=('GET', 'POST'))
@login_required
def create_tag():
    form = forms.TagForm()
    if form.validate_on_submit():
        models.Tag.create(tag=form.tag.data.strip())
        flash("Tag created.", "success")
        models.EntryTag.tag_current_entries(models.Tag.get(tag=form.tag.data.strip()))
        return redirect(url_for('index'))
    return render_template('create_tag.html', form=form)

@app.route('/entries/<tag>')
@login_required
def entries_by_tag(tag):
    display_entries = []
    try:
        tagged_entries = set((models.Entry.select().join(models.EntryTag).join(models.Tag).where(models.Tag.tag == tag).order_by(models.Entry.date.desc())))
    except models.DoesNotExist:
        redirect(url_for('index'))
    else:
        for entry in tagged_entries:
            entry_tags = set((models.Tag.select().join(models.EntryTag).where(models.EntryTag.entry == entry)))
            display_entries.append([entry, entry_tags])
    return render_template('index.html', entries=display_entries)

@app.route('/tags')
@login_required
def view_tags():
    tags = set(models.Tag.select())
    return render_template('view_tags.html', tags=tags)

@app.route('/tags/<tag>', methods=('GET', 'POST'))
@login_required
def delete_tag(tag):
    try: 
        tag_to_delete = models.Tag.get(tag=tag)
        tag_relationship = models.EntryTag.get(tag=tag_to_delete)
    except models.DoesNotExist:
        abort(404)
    else:
        tag_relationship.delete_instance()
        tag_to_delete.delete_instance()
        flash("Tag deleted.", "success")
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG, host=HOST, port=PORT)