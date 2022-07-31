import sys
import json
from datetime import datetime, timedelta


def exit_on_error(error_message):

    print(error_message)
    sys.exit(1)


def validate_input_date(date):
    try:
        dt = datetime.strptime(date + ' 00:00:00,76', '%Y-%m-%d %H:%M:%S,%f')
        return True
    except ValueError:
        return False


def validate_environment(environment):
    if environment not in ['dev', 'prod']:
        return False
    return True


def get_session_config(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)

    return config


def get_weekdate_range(date, date_format='%Y-%m-%d'):

    if not isinstance(date, datetime):
        date = datetime.strptime(date, date_format)
        
    monday = date - timedelta(days = date.weekday())
    next_sunday = date + timedelta(days = 6)

    monday = datetime.strftime(monday, date_format)
    next_sunday = datetime.strftime(next_sunday, date_format)

    return monday, next_sunday


def get_month_name(date, date_format='%Y-%m-%d'):

    if not isinstance(date, datetime) or not isinstance(date, datetime.date):
        date = datetime.strptime(date, date_format)
        
    month_name = date.strftime('%b')

    return month_name


def get_year(date, date_format='%Y-%m-%d'):

    if not isinstance(date, datetime) or not isinstance(date, datetime.date):
        date = datetime.strptime(date, date_format)
        
    year = date.year

    return year

def select_all(cursor, table):
    cols_query = 'SHOW COLUMNS FROM ' + table
    data_query = 'SELECT * FROM ' + table

    cursor.execute(cols_query)
    cols = cursor.fetchall()
    columns = [col[0] for col in cols]

    cursor.execute(data_query)
    data = cursor.fetchall()

    return columns, data
