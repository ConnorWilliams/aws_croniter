import pytest

from datetime import datetime

from src.aws_croniter import CronExpression

# class TestGetNext(object):
#     @pytest.mark.parametrize("start_time, expression, expected", [
#         (
#             datetime(2017, 1, 1, 0, 0, 0),
#             "* * * * * *",
#             datetime(2017, 1, 1, 0, 0, 1)
#         ),
#         (
#             datetime(2017, 1, 1, 0, 0, 0),
#             "20 * * * * *",
#             datetime(2017, 1, 1, 0, 20, 0)
#         ),
#     ])
#     def test_get_next(self, start_time, expression, expected):
#         awscron_iter = croniter(expression, start_time, return_type=float, day_or=True)
#         result = awscron_iter.get_next(return_type=datetime)
#         assert result == expected

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
                    ['?'],
                    ['*']
                ]
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
                    ['?'],
                    [2018]
                ]
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
                    ['?'],
                    ['*']
                ]
            )
        ),
    ])
    def test_expand(self, expression, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.expand(obj_expression.fields)
        assert result == expected
        # assert 1==2

class TestExpandField(object):
    @pytest.mark.parametrize("expression, field_name, field, expected", [
        (
            "* * * * * ? *", 'minute', '5-10', [5, 6, 7, 8, 9, 10]
        ),
        (
            "* * * * * ? *", 'day_of_week', 'mon-wed', [2, 3, 4]
        ),
        (
            "* * * * * ? *", 'day_of_week', 'sUn-thU', [1, 2, 3, 4, 5]
        ),
        (
            "* * * * * ? *", 'day_of_week', 'sUn-thU/2', [1, 3, 5]
        ),
    ])
    def test_expand_field(self, expression, field_name, field, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.expand_field(field_name, field)
        assert result == expected
        # assert 1==2

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
    ])
    def test_expand(self, expression,  value, field_name, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.calendar_to_num(field_name, value)
        assert result == expected
        # assert 1==2
