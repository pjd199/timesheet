"""Data storage, using AWS dynamodb database via pynamodb."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from json import dumps, loads
from typing import Any

from pynamodb.attributes import (
    Attribute,
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.constants import STRING
from pynamodb.models import Model

from pycaltime.config import config


@dataclass
class Timesheet:
    """Timesheet dataclass."""

    work: int = 0
    holiday: int = 0
    bank: int = 0
    sick: int = 0

    def __init__(
        self, work: int = 0, holiday: int = 0, bank: int = 0, sick: int = 0
    ) -> None:
        """Initializer.

        Args:
            work (int, optional): working minutes. Defaults to 0.
            holiday (int, optional): holiday minutes. Defaults to 0.
            bank (int, optional): bank holiday minutes. Defaults to 0.
            sick (int, optional): sick leave minutes. Defaults to 0.
        """
        self.work = work
        self.holiday = holiday
        self.bank = bank
        self.sick = sick

    def total(self) -> int:
        """Total minutes recorded in timesheet.

        Returns:
            int: total minutes
        """
        return self.work + self.holiday + self.bank + self.sick

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Timesheet(work={self.work},holiday={self.holiday},"
            f"bank={self.bank},sick={self.sick})"
        )


class TimesheetDict(Attribute):
    """Timesheet dict Attribute."""

    attr_type = STRING

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self._data: dict[date, Timesheet] = {}

    def __getitem__(self, key: date) -> Timesheet:
        """Retrieve a Timesheet from the dict.

        Args:
            key (date): date of timesheet

        Returns:
            Timesheet: the timesheet
        """
        return self._data[key]

    def __setitem__(self, key: date, value: Timesheet) -> None:
        """Store a Timesheet in the dict.

        Args:
            key (date): the date
            value (Timesheet): the timesheet
        """
        self._data[key] = value

    def __iter__(self) -> Iterator[Timesheet]:
        """Iterator returning Timesheets in ascending date order.

        Yields:
            Iterator[Timesheet]: the timesheets
        """
        yield from sorted(self._data.items())

    def serialize(self, value: dict[date, Timesheet]) -> str:
        """Serialize value for dynamodb.

        Args:
            value (dict[date, Timesheet]): values to serialize.

        Returns:
            str: serialized values
        """
        result: dict[str, dict[str, int]] = {}
        for week, timesheet in value.items():
            key = f"Y{week.year:02d}M{week.month:02d}D{week.day:02d}"
            result[key] = {
                "work": timesheet.work,
                "holiday": timesheet.holiday,
                "bank": timesheet.bank,
                "sick": timesheet.sick,
            }
        return dumps(result)

    def deserialize(self, value: str) -> dict[date, Timesheet]:
        """Deserialize dynamodb values to a dict.

        Args:
            value (str): from dynamodb

        Returns:
            dict[date, Timesheet]: the dict
        """
        data = loads(value)

        result: dict[date, Timesheet] = {}
        for week, values in data.items():
            key = date(int(week[1:5]), int(week[6:8]), int(week[9:11]))
            result[key] = Timesheet(**values)
        return result


class JobData(MapAttribute):
    """Job Data Attribute."""

    hashtag = UnicodeAttribute()
    name = UnicodeAttribute()
    short_name = UnicodeAttribute()
    contracted_hours = NumberAttribute()
    annual_holiday_hours = NumberAttribute()
    pro_rata_bank_holiday = BooleanAttribute()
    employment_start = UTCDateTimeAttribute()
    employment_end = UTCDateTimeAttribute()
    timesheets = TimesheetDict()


class UserData(Model):
    """DynamoDB UserData Table."""

    class Meta:
        """Metadata."""

        table_name = "PyCalTimeUserData"
        region = config.AWS_REGION

    id = UnicodeAttribute(hash_key=True)
    jobs = ListAttribute(of=JobData)
    view_past_weeks = NumberAttribute(default=4)
    view_future_weeks = NumberAttribute(default=2)
    last_updated = UTCDateTimeAttribute()


# initialise the database
def initialize_database() -> None:
    """Initialize the database."""
    if not UserData.exists():
        UserData.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
