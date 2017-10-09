#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function
from time import time
import datetime
from datetime import timedelta
import math

FIELD_NAMES = [
    'second', 'minute', 'hour', 'day_of_month', 'month', 'day_of_week', 'year'
]

RANGES = {
    'second': {'min': 0, 'max': 59},
    'minute': {'min': 0, 'max': 59},
    'hour': {'min': 0, 'max': 23},
    'day_of_month': {'min': 1, 'max': 31, 0: 1},
    'month': {'min': 1, 'max': 12, 0: 1},
    'day_of_week': {'min': 1, 'max': 7, 0: 1},
    'year': {'min': 1970, 'max': 2199}
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

        self.expanded_expression, self.day_wk_numbers =\
            self.expand(self.fields)
        return None

    @classmethod
    def expand(self, fields):
        """
            Expands the provided cron expression
        """

        expanded_fields = []
        day_wk_numbers = {}

        for field_name, field in zip(FIELD_NAMES, fields):
            expanded_field, field_day_wk_numbers =\
                self.expand_field(field_name, field)
            expanded_fields.append(expanded_field)
            day_wk_numbers.update(field_day_wk_numbers)
        return expanded_fields, day_wk_numbers

    @classmethod
    def expand_field(self, field_name, field):
        """
            Expands the provided field
        """
        if field is None:
            return [0], {}

        field_execution_times = []

        values = field.split(',')
        for value in values:
            value_execution_times, day_wk_numbers =\
                self.expand_value(field_name, value)
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
            'year', 'day_of_week', 'month', 'day_of_month', 'hour', 'minute',
            'second'
        ]
        cron_field_names = [
            'second', 'minute', 'hour', 'day_of_month', 'month', 'day_of_week',
            'year'
        ]
        date_1 = self.split_date(date_1)
        date_2 = self.split_date(date_2)

        for field_name, d_1, d_2 in zip(datetime_field_names, date_1, date_2):
            execution_times = self.obj_expression.expanded_expression[
                cron_field_names.index(field_name)
            ]

            # If * then it always executes
            if execution_times == ['*']:
                continue

            # If day_of_week# then compare cron execution days
            # with range execution days.
            elif(
                field_name == 'day_of_week' and
                self.obj_expression.day_wk_numbers != {}
            ):
                range_day_wk_numbers =\
                    self.range_day_wk_numbers(date_1, date_2)
                cron_day_wk_numbers = self.obj_expression.day_wk_numbers

                for weekday in set(range_day_wk_numbers).intersection(
                    set(cron_day_wk_numbers)
                ):
                    if not self.common_element(
                        cron_day_wk_numbers[weekday],
                        range_day_wk_numbers[weekday]
                    ):
                        return False

            # Else compare cron execution times with range times.
            else:
                d_1, d_2 = map(int, [d_1, d_2])
                d_range = [d_1 % RANGES[field_name]['max']]

                # Cycle from d_1 to d_2
                while(
                    d_1 % RANGES[field_name]['max'] !=
                    d_2 % RANGES[field_name]['max']
                ):
                    d_1 = d_1+1
                    if d_1 % RANGES[field_name]['max'] == 0:
                        d_range.append(RANGES[field_name]['max'])
                    else:
                        d_range.append(d_1 % RANGES[field_name]['max'])

                # If the cron job has no execution time within this range
                if not self.common_element(execution_times, d_range):
                    return False
        # All cron fields have at least 1 execution time within this range
        return True

    def range_day_wk_numbers(self, date_1, date_2):
        day_wk_numbers = {}
        date_1 = datetime.datetime(date_1[0], date_1[2], date_1[3])
        date_2 = datetime.datetime(date_2[0], date_2[2], date_2[3])
        for date in self.daterange(date_1, date_2):
            weekday = (date.isoweekday() % 7) + 1
            if weekday not in day_wk_numbers:
                day_wk_numbers[weekday] = set()
            day_wk_numbers[weekday].add(int(math.ceil(float(date.day)/7)))
        # print(day_wk_numbers)
        return day_wk_numbers

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)+1):
            yield start_date + timedelta(n)

    def split_date(self, date):
        list_date = list(map(int, date.split(' ')))
        weekday = (
            datetime.date(
                list_date[0],
                list_date[1],
                list_date[2]
            ).isoweekday() % 7) + 1
        list_date.insert(1, weekday)
        return list_date

    def common_element(self, list_1, list_2):
        return any(True for element in list_1 if element in list_2)
