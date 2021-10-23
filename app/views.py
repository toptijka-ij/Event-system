import requests
from flask import render_template, request, redirect, flash, url_for
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.exc import DataError, OperationalError
from werkzeug.urls import url_parse

from . import app
from .forms import LoginForm, RegistrationForm
from .models import Event, User, AddError, db
from .utilities import form_check_datetime, allowed_users, from_datetime_to_date_and_time


@app.route('/')
@app.route('/index')
@app.route('/events/<string:status>')
def index(status='all'):
    if status == 'upcoming':
        events = Event.upcoming_events()
    else:
        events = Event.get_all()
    return render_template('event/list_events.html', events=events)


@app.route('/events/create', methods=['GET', 'POST'], endpoint='create')
@login_required
@allowed_users(allowed_roles=['admin', ])
def events_create():
    available_authors = requests.get('http://127.0.0.1:8000/api/authors/').json()
    if request.method == 'POST':
        try:
            name = request.form['name']
            ev_date = form_check_datetime(request.form['date'], request.form['time'])
            authors = request.form.getlist('authors')
            Event.add_event(name, ev_date, authors=authors)
        except DataError:
            flash(u'Мероприятие не добавлено. Укажите коррекные дату и время проведения мероприятия.', 'error')
            return render_template('event/create_event.html')
        except AddError:
            flash(u'Мероприятие не добавлено', 'error')
            return render_template('event/create_event.html')
        else:
            flash(u'Мероприятие успешно добавлено', 'success')
            return redirect('/')
    else:
        return render_template('event/create_event.html', authors=available_authors)


@app.route('/events/<int:event_id>/update', methods=['GET', 'POST'], endpoint='update')
@login_required
@allowed_users(allowed_roles=['admin', ])
def events_update(event_id):
    event = Event.query.get_or_404(event_id)
    # available_authors = requests.get('http://127.0.0.1:8000/api/authors/').json()
    if request.method == 'POST':
        event.name = request.form['name']
        event.ev_date = form_check_datetime(request.form['date'], request.form['time'])
        event.authors = request.form.getlist('authors')
        try:
            db.session.commit()
        except:
            flash(u'Не удалось обновить мероприятие', 'error')
            return render_template('event/update_event.html')
        else:
            flash(u'Мероприятие успешно обновлено', 'success')
            return redirect('/')
    else:
        ev_date, ev_time = from_datetime_to_date_and_time(event.ev_date)
        return render_template('event/update_event.html', event=event, ev_time=ev_time, ev_date=ev_date)


@app.route('/events/<int:event_id>/delete', methods=['GET', 'POST'], endpoint='delete')
@login_required
@allowed_users(allowed_roles=['admin', ])
def events_delete(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        try:
            db.session.delete(event)
            db.session.commit()
        except:
            flash(u'Не удалось отменить мероприятие', 'error')
            return render_template('event/create_event.html')
        else:
            flash(u'Мероприятие успешно отменено', 'success')
            return redirect('/')
    else:
        return render_template('event/delete_event.html', event=event)


@app.route('/events/<int:id>')
def event_detail(id):
    event = Event.query.get_or_404(id)
    return render_template('event/detail_event.html', event=event)


@app.route('/events/<int:id>/register')
@login_required
def register_user_on_event(id):
    event = Event.query.get_or_404(id)
    try:
        event.add_visitor(current_user)
    except AddError:
        flash(u'Регистрация не удалась', 'error')
        return redirect(f'/events/{event.id}')
    else:
        flash(u'Вы успешно зарегистрировались', 'success')
        return redirect(f'/events/{event.id}')


@app.route('/user/events')
def user_events():
    return render_template('user/user_events.html', events=current_user.events, user=current_user)


@app.route('/user/<int:user_id>/event/<int:event_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user_event_registration(user_id, event_id):
    event = Event.query.get_or_404(event_id)
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            User.delete_event(user, event)
        except OperationalError:
            flash(u'Вашу запись на мероприятие не удалось удалить', 'error')
            return redirect('/user')
        flash(u'Ваша запись на мероприятие отменена', 'success')
        return render_template('user/user_events.html', events=user.events, user=user)
    else:
        return render_template('user/delete_event_registration.html', event=event)


@app.route('/user/<int:user_id>/update', methods=['GET', 'POST'])
@login_required
def update_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            user.username = request.form['username']
            user.email = request.form['email']
            db.session.commit()
        except:
            flash(u'Обновить данные не удалось', 'error')
            return redirect(f'/user/{user_id}/update')
        else:
            flash(u'Данные успешно обновлены', 'success')
            return redirect('/')
    else:
        return render_template('user/user_profile_update.html', user=user)


@app.route('/user/<int:user_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            flash(u'Не удалось удалить профиль', 'error')
            return redirect(f'/user/{user_id}/delete')
        else:
            flash(u'Профиль удален', 'success')
            return redirect('/')
    else:
        return render_template('user/user_profile_delete.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(u'Недопустимое имя пользователся или пароль', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        flash(u'Вы успешно вошли в систему', 'success')
        return redirect(next_page)
    return render_template('user/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # try:
        User.add_new_user(username=form.username.data, email=form.email.data, password=form.password.data)
        # except AddError:
        #     flash(u'Регистрация не удалась', 'error')
        # else:
        #     flash(u'Вы успешно зарегистрировались', 'success')
        return redirect(url_for('login'))
    return render_template('user/register.html', title='Register', form=form)
