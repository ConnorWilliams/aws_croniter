import pytest

from datetime import datetime

from src.aws_croniter import CronExpression, Croniter


class TestExecutesBetween(object):
    @pytest.mark.parametrize("expression, date_1, date_2, expected", [
        (
            "2 * * ? * * *",
            datetime(2017, 1, 1, 0, 0, 1),
            datetime(2017, 1, 1, 0, 0, 3),
            True
        ),
        (
            "5 * * ? * * *",
            datetime(2017, 1, 1, 0, 0, 58),
            datetime(2017, 1, 1, 0, 0, 2),
            False
        ),
        (
            "0 0 * ? * Tue *",
            datetime(2018, 1, 1, 0, 0, 0),
            datetime(2018, 1, 5, 0, 0, 0),
            True
        ),
        (
            "0 0 * ? * Tue *",
            datetime(2018, 1, 3, 0, 0, 0),
            datetime(2018, 1, 6, 0, 0, 0),
            False
        ),
        (
            "0 0 * 4-8 * ? 2017",
            datetime(2017, 1, 1, 0, 0, 0),
            datetime(2018, 1, 5, 0, 0, 0),
            True
        ),
        (
            "* * * ? * Sat 2018",
            datetime(2018, 1, 19, 0, 0, 0),
            datetime(2018, 1, 22, 0, 0, 0),
            True
        ),
        (
            "* * * ? * Sat#3 2018",
            datetime(2018, 1, 19, 0, 0, 0),
            datetime(2018, 1, 22, 0, 0, 0),
            True
        ),
        (
            "* * * ? * Sat#1 2018",
            datetime(2018, 1, 19, 0, 0, 0),
            datetime(2018, 1, 22, 0, 0, 0),
            False
        ),
    ])
    def test_executes_between(self, expression, date_1, date_2, expected):
        obj_expression = CronExpression(expression)
        awscron_iter = Croniter(obj_expression)
        result = awscron_iter.executes_between(date_1, date_2)
        assert result == expected


class TestExpand(object):
    @pytest.mark.parametrize("expression, expected", [
        (
            "* * * * * ? *",
            (
                [
                    ['*'],
                    ['*'],
                    ['*'],
                    ['*'],
                    ['*'],
                    ['*'],
                    ['*']
                ],
                {}
            )
        ),
        (
            "0 59 5/5 10-16 2-10/2 ? 2018",
            (
                [
                    [0],
                    [59],
                    [5, 10, 15, 20],
                    [10, 11, 12, 13, 14, 15, 16],
                    [2, 4, 6, 8, 10],
                    ['*'],
                    [2018]
                ],
                {}
            )
        ),
        (
            "1,2,5,58 2,3 1-5/2,18/3 1-5,10-13 1-5/2,8-11 ? *",
            (
                [
                    [1, 2, 5, 58],
                    [2, 3],
                    [1, 3, 5, 18, 21],
                    [1, 2, 3, 4, 5, 10, 11, 12, 13],
                    [1, 3, 5, 8, 9, 10, 11],
                    ['*'],
                    ['*']
                ],
                {}
            )
        ),
        (
            "0 0 * ? * THU#3 *",
            (
                [
                    [0],
                    [0],
                    ['*'],
                    ['*'],
                    ['*'],
                    [5],
                    ['*']
                ],
                {5: {3}}
            )
        ),
        (
            "0 0 * ? * Mon-ThU#1-3 *",
            (
                [
                    [0],
                    [0],
                    ['*'],
                    ['*'],
                    ['*'],
                    [2, 3, 4, 5],
                    ['*']
                ],
                {
                    2: {1, 2, 3},
                    3: {1, 2, 3},
                    4: {1, 2, 3},
                    5: {1, 2, 3},
                }
            )
        ),
    ])
    def test_expand(self, expression, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.expand(obj_expression.fields)
        assert result == expected


class TestExpandField(object):
    @pytest.mark.parametrize("expression, field_name, field, expected", [
        (
            "* * * * * ? *", 'minute', '5-10', ([5, 6, 7, 8, 9, 10], {})
        ),
        (
            "* * * * * ? *", 'day_of_week', 'mon-wed', ([2, 3, 4], {})
        ),
        (
            "* * * * * ? *", 'day_of_week', 'sUn-thU', ([1, 2, 3, 4, 5], {})
        ),
        (
            "* * * * * ? *", 'day_of_week', 'sUn-thU/2', ([1, 3, 5], {})
        ),
    ])
    def test_expand_field(self, expression, field_name, field, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.expand_field(field_name, field)
        assert result == expected


class TestCalendarToNum(object):
    @pytest.mark.parametrize("expression, value, field_name, expected", [
        (
            '* * * * * ? *', 'mon', 'day_of_week', '2'
        ),
        (
            '* * * * * ? *', 'mon-wed', 'day_of_week', '2-4'
        ),
        (
            '* * * * * ? *', 'sun-thu', 'day_of_week', '1-5'
        ),
        (
            '* * * * * ? *', 'mon-fri/2', 'day_of_week', '2-6/2'
        ),
        (
            '* * * * * ? *', 'jan', 'month', '1'
        ),
        (
            '* * * * * ? *', 'feb-jun', 'month', '2-6'
        ),
        (
            '* * * * * ? *', 'feb-oct/2', 'month', '2-10/2'
        ),
        (
            '* * * * * ? *', '1', 'minute', '1'
        ),
        (
            '0 0 * ? * THU#3 *', 'THU#3', 'day_of_week', '5#3'
        ),
        (
            '0 0 * ? * Mon-ThU#1-3 *', 'Mon-ThU#1-3', 'day_of_week', '2-5#1-3'
        ),
    ])
    def test_expand(self, expression, value, field_name, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.calendar_to_num(field_name, value)
        assert result == expected
