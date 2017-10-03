import pytest

from datetime import datetime

from src.aws_croniter import croniter

class TestGetNext(object):
    @pytest.mark.parametrize("start_time, expression, expected", [
        (
            datetime(2017, 1, 1, 0, 0, 0),
            "* * * * * *",
            datetime(2017, 1, 1, 0, 0, 1)
        ),
        (
            datetime(2017, 1, 1, 0, 0, 0),
            "20 * * * * *",
            datetime(2017, 1, 1, 0, 20, 0)
        ),
    ])
    def test_get_next(self, start_time, expression, expected):
        awscron_iter = croniter(expression, start_time, return_type=float, day_or=True)
        result = awscron_iter.get_next(return_type=datetime)
        assert result == expected

class TestExpand(object):
    @pytest.mark.parametrize("start_time, expression, expected", [
        (
            datetime(2017, 1, 1, 0, 0, 0),
            "* * * * * *",
            (
                [['*'], ['*'], ['*'], ['*'], ['*'], ['*']],
                {}
            )
        ),
        (
            datetime(2017, 1, 1, 0, 0, 0),
            "20 * * * * *",
            (
                [[20], ['*'], ['*'], ['*'], ['*'], ['*']],
                {}
            )
        ),
        (
            datetime(2017, 1, 1, 0, 0, 0),
            "* * * * thu#3 *",
            (
                [['*'], ['*'], ['*'], ['*'], [5], ['*']],
                {
                    5: {3}
                }
            )
        ),
    ])
    def test_expand(self, start_time, expression, expected):
        awscron_iter = croniter(expression, start_time)
        result = awscron_iter.expand(expression)
        assert result == expected
