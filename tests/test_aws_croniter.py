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
            "* * * * * * *",
            (
                [['*'], ['*'], ['*'], ['*'], ['*'], ['*'], ['*']],
                {}
            )
        ),
        (
            "20 * * * * *",
            (
                [[0], [20], ['*'], ['*'], ['*'], ['*'], ['*']],
                {}
            )
        ),
        (
            "5-50/10 * * * * thu#3 *",
            (
                [[5, 15, 25, 35, 45], ['*'], ['*'], ['*'], ['*'], [5], ['*']],
                {
                    5: {3}
                }
            )
        ),
    ])
    def test_expand(self, expression, expected):
        obj_expression = CronExpression(expression)
        result = obj_expression.expand(obj_expression.fields)
        assert result == expected
        # assert 1==2
