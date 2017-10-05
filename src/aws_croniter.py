#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function
import re
from time import time
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzutc
import calendar

OLD_FIELDS = ['minute', 'hour', 'day_of_month', 'month', 'day_of_week', 'year']
FIELD_NAMES = ['second', 'minute', 'hour', 'day_of_month', 'month', 'day_of_week', 'year']

re_range_optional_slash = re.compile(r'^([^-]+)-([^-/]+)(/(.*))?$')
star_or_int_re = re.compile(r'^(\d+|\*)$')
VALID_LEN_EXPRESSION = [6, 7]

RANGES = {
    'second': {
        'min': 0,
        'max': 59
    },
    'minute': {
        'min': 0,
        'max': 59
    },
    'hour': {
        'min': 0,
        'max': 23
    },
    'day_of_month': {
        'min': 1,
        'max': 31,
        0: 1
    },
    'month': {
        'min': 1,
        'max': 12,
        0: 1
    },
    'day_of_week': {
        'min': 1,
        'max': 7,
        0: 1
    },
    'year': {
        'min': 1970,
        'max': 2199
    }
}

class CroniterError(ValueError):
    pass


class CroniterBadCronError(CroniterError):
    pass


class CroniterBadDateError(CroniterError):
    pass


class CroniterNotAlphaError(CroniterError):
    pass


class CronExpression(object):
    CALENDAR = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'sun': 1, 'mon': 2, 'tue': 3, 'wed': 4, 'thu': 5, 'fri': 6,
        'sat': 7,
    }

    bad_length = 'Exactly 6 or 7 columns has to be specified for iterator' \
                 'expression.'

    def __init__(self, expression):
        expression = expression.split()
        if len(expression) == 6:
            second = None
            minute, hour, day_of_month, month, day_of_week, year = expression
        elif len(expression) == 7:
            second, minute, hour, day_of_month, month, day_of_week, year =\
                expression
        else:
            raise CroniterBadCronError(self.bad_length)

        self.fields = [
            second, minute, hour, day_of_month, month, day_of_week, year
        ]

        if [day_of_month, day_of_week].count('?') is not 1:
            raise CroniterBadCronError(
                '''
                You cannot specify a value in the day_of_month and in the
                day_of_week fields in the same cron expression. If you specify
                a value in one of the fields, you must use a ? (question mark)
                in the other field.
                '''
            )

        self.expanded_expression, self.day_wk_numbers = self.expand(self.fields)
        return None

    @classmethod
    def expand(self, fields):
        """
            Expands the provided cron expression
        """

        expanded_fields = []
        day_wk_numbers = {}

        for field_name, field in zip(FIELD_NAMES, fields):
            expanded_field, field_day_wk_numbers = self.expand_field(field_name, field)
            expanded_fields.append(expanded_field)
            day_wk_numbers.update(field_day_wk_numbers)
        return expanded_fields, day_wk_numbers

    @classmethod
    def expand_field(self, field_name, field):
        """
            Expands the provided field
        """
        if field == None:
            return [0], {}

        field_execution_times = []

        values = field.split(',')
        for value in values:
            value_execution_times, day_wk_numbers = self.expand_value(field_name, value)
            field_execution_times += value_execution_times

        field_execution_times.sort()
        return field_execution_times, day_wk_numbers

    @classmethod
    def expand_value(self, field_name, value):
        """
            Recursive boi
        """
        # Convert month or day names to their corresponding integers
        value = self.calendar_to_num(field_name, value)
        day_wk_numbers = {}

        if field_name == 'day_of_week':
            if '#' in value:
                value, pound, wk_numbers = value.partition('#')
                expanded_value, tmp = self.expand_value('', value)
                expanded_wk_numbers, tmp = self.expand_value('', wk_numbers)
                for day in expanded_value:
                    if day not in day_wk_numbers:
                        day_wk_numbers[day] = set()
                    for wk_number in expanded_wk_numbers:
                        day_wk_numbers[day].add(int(wk_number))

        # If we have an increment but not a range
        if '/' in value:
            value, slash, increment = value.partition('/')
            if '-' not in value:
                # Translate to a range.
                value = self.convert_to_range(value, field_name)
            low, high = value.split('-')
            low, high, increment = map(int, [low, high, increment])
            return list(range(low, high+1, increment)), day_wk_numbers

        # If we just have a range:
        elif '-' in value:
            low, high = value.split('-')
            low, high = map(int, [low, high])
            return list(range(low, high+1)), day_wk_numbers

        # If we just have a number
        elif value.isdigit():
            return [int(value)], day_wk_numbers

        # If we have l
        elif value.lower() == 'l':
            return [RANGES[field_name]['max']], day_wk_numbers

        # If we have * or ?
        else:
            return '*', day_wk_numbers

    @classmethod
    def convert_to_range(self, value, field_name):
        if value == '*':
            return '{}-{}'.format(
                RANGES[field_name]['min'],
                RANGES[field_name]['max']
            )
        elif int(value):
            return '{}-{}'.format(
                value,
                RANGES[field_name]['max']
            )

    @classmethod
    def calendar_to_num(self, field_name, value):
        pound = ''
        wk_numbers = ''
        if '#' in value:
            value, pound, wk_numbers = value.partition('#')

        if field_name in ['month', 'day_of_week']:
            value, slash, increment = value.partition('/')
            low, dash, high = value.partition('-')
            low = low.lower()
            high = high.lower()

            if low in list(self.CALENDAR.keys()):
                low = self.CALENDAR[low]
            if high in list(self.CALENDAR.keys()):
                high = self.CALENDAR[high]

            low, high = map(str, [low, high])
            return low+dash+high+slash+increment+pound+wk_numbers
        else:
            return value


class Croniter(object):
    DAYS = (
        31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
    )

    def __init__(self, obj_expression, start_time=None):
        self.start_time = start_time
        self.obj_expression = obj_expression

        # Set start time to now
        if self.start_time is None:
            self.start_time = time()

    def executes_between(self, date_1, date_2):
        datetime_field_names = [
            'year', 'month', 'day_of_month', 'hour', 'minute', 'second'
        ]
        date_1 = date_1.split(' ')
        date_2 = date_2.split(' ')
        for field_name, d_1, d_2 in zip(datetime_field_names, date_1, date_2):
            d_1, d_2 = map(int, [d_1, d_2])
            print(d_1, d_2)
            d_range = []
            while d_1%RANGES[field_name]['max'] != d_2%RANGES[field_name]['max']:
                if d_1%RANGES[field_name]['max'] == 0:
                    d_range.append(RANGES[field_name]['max'])
                else:
                    d_range.append(d_1%RANGES[field_name]['max'])
                d_1 = d_1+1
            # if nothing in d_range is in self.obj_expression.expanded_expression.index(field_name):
                # return False

        return True
