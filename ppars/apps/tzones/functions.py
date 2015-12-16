from datetime import datetime
from pytz import timezone
from pytz import utc

from celery.schedules import crontab


def crontab_with_correct_tz(hour, minute):
    """
    :param hour
    :param minute
    Params hours and minutes of local time zone US/Eastern

    :return: the result of function crontab
    """
    # getting current time in Eastern
    eastern_time_today = timezone('US/Eastern').localize(datetime.utcnow())

    # setting hours and minutes
    eastern_time = eastern_time_today.replace(hour=hour, minute=minute)

    # back translation eastern time to UTC
    utc_datetime = eastern_time.astimezone(utc)

    return crontab(hour=utc_datetime.hour, minute=utc_datetime.minute)