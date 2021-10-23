from datetime import datetime, timedelta
from functools import wraps

from flask_login import current_user
from sqlalchemy.exc import DataError


def form_check_datetime(my_date, my_time):
    res = datetime.strptime(my_date + ' ' + my_time, '%Y-%m-%d %H:%M')
    if res - datetime.now() >= timedelta(days=1):
        return res
    else:
        raise DataError


def from_datetime_to_date_and_time(my_datedime: datetime):
    return my_datedime.date(), my_datedime.time()


def allowed_users(allowed_roles=[]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if current_user.is_admin:
                return func(*args, **kwargs)
            else:
                raise PermissionError

        return wrapper

    return decorator
