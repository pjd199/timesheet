"""Utility functions."""

from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any, TypeVar

_T = TypeVar("_T")


def include_from_dict(cls: type[_T]) -> type[_T]:
    """A decorator that adds a 'from_dict' class method to a dataclass."""

    @classmethod
    def from_dict(cls: type[_T], data: dict[str, Any]) -> _T:
        """Creates an instance of the dataclass from a dictionary."""
        field_names = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)

    cls.from_dict = from_dict
    return cls


def date_range(start: date, stop: date, step: timedelta) -> Iterator[date]:
    """Like range, but for dates.

    Args:
        start (date): start date
        stop (date): stop date
        step (timedelta): step

    Yields:
        date: range of dates from start to stop
    """
    current = start
    if step >= timedelta(seconds=0):
        # ascending
        while current < stop:
            yield current
            current += step
    else:
        # descending
        while current > stop:
            yield current
            current += step


def first_day_of_the_week(t: date) -> date:
    """Calculate the first day of the week, ie the Monday of that week."""
    return t - timedelta(days=t.weekday())


def first_day_of_the_month(t: date) -> date:
    """Find the date of the first day of the month.

    Args:
        t (date): the input date.

    Returns:
        date: the date of the first day of the month
    """
    return t.replace(day=1)


def first_day_of_the_next_month(t: date) -> date:
    """Find the first day of the next month.

    Args:
        t (date): the input date

    Returns:
        date: the first day of the next month
    """
    if t.month == 12:
        return date(t.year + 1, month=1, day=1)
    return date(t.year, t.month + 1, day=1)


def first_day_of_the_previous_month(t: date) -> date:
    """Find the first day of the previous month.

    Args:
        t (date): the input date

    Returns:
        date: the date of the 1st of the previous month
    """
    if t.month == 1:
        return date(t.year - 1, month=12, day=1)
    return date(t.year, t.month - 1, day=1)


def iterate_weeks(start: date, finish: date) -> Iterator[date]:
    """Yield dates every 7 days between start and finish.

    Args:
        start (date): start date
        finish (date): finish date

    Yields:
        date: weekly dates from start to finish (excluding finish)
    """
    result = start
    while result < finish:
        yield result
        result += timedelta(weeks=1)
