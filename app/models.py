from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


class AddError(SQLAlchemyError):
    pass


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', backref='role')

    def __str__(self):
        return self.name


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id'), nullable=False)

    @property
    def role(self):
        role_obj = Role.query.filter_by(id=self.role_id).first()
        return role_obj

    @property
    def is_admin(self):
        return True if self.role.name == 'admin' else False

    def __repr__(self):
        return f'<User {self.id}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def add_new_user(username, email, password):
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            user.role_id = Role.query.filter_by(name='guest').first().id
            db.session.add(user)
            db.session.commit()
            return user
        except:
            raise AddError

    @staticmethod
    def delete_event(user, event):
        try:
            user.events.remove(event)
            db.session.commit()
        except:
            raise OperationalError


users_events = db.Table('users_events',
                        db.Column('events_id', db.Integer, db.ForeignKey('events.id', ondelete='CASCADE')),
                        db.Column('users_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
                        )


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ev_date = db.Column(db.DateTime, nullable=False)
    guests = db.Column(ARRAY(db.String(100)))
    users = db.relationship("User", secondary=users_events, passive_deletes='all',
                            backref=db.backref('events', lazy='dynamic'))

    def __repr__(self):
        return f'<Event {self.id}>'

    @property
    def status(self):
        return 'ожидается' if self.ev_date > datetime.now() else 'проведено'

    @staticmethod
    def upcoming_events():
        return [event for event in Event.get_all() if event.status == 'ожидается']

    @staticmethod
    def get_all():
        return Event.query.order_by(Event.ev_date).all()

    @staticmethod
    def add_event(name, ev_date, authors=None):
        try:
            event = Event(name=name, ev_date=ev_date, guests=authors)
            db.session.add(event)
            db.session.commit()
        except:
            raise AddError

    def add_visitor(self, user):
        try:
            self.users.append(user)
            db.session.add(self)
            db.session.commit()
        except:
            return AddError
