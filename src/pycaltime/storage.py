from pynamodb.attributes import (
    Attribute,
    UnicodeAttribute,
    UTCDateTimeAttribute,
    MapAttribute,
    NumberAttribute,
    ListAttribute,
    BooleanAttribute,
)
from datetime import date
from pynamodb.models import Model
from os import environ
from pynamodb.constants import MAP, STRING
from typing import Any
from pycaltime.config import AWS_DEFAULT_REGION

from json import dumps, loads

from dataclasses import dataclass

# class Timesheet(MapAttribute):
#     work = NumberAttribute(default=0)  # minutes
#     holiday = NumberAttribute(default=0)  # minutes
#     bank = NumberAttribute(default=0)  # minutes
#     sick = NumberAttribute(default=0)  # minutes

#     def add_time(self, category: str, minutes: int) -> None:
#         if category in ["work", "holiday", "bank", "sick"]:
#             current_value = getattr(self, category) or 0
#             setattr(self, category, current_value + minutes)

#     def total(self) -> int:
#         return self.work + self.holiday + self.bank + self.sick


@dataclass
class Timesheet:
    work = 0
    holiday = 0
    bank = 0
    sick = 0

    def __init__(self, work=0, holiday=0, bank=0, sick=0):
        self.work = work
        self.holiday = holiday
        self.bank = bank
        self.sick = sick

    def __repr__(self):
        return f"Timesheet(work={self.work},holiday={self.holiday},bank={self.bank},sick={self.sick})"

    # def add_time(self, category: str, minutes: int) -> None:
    #     if category in ["work", "holiday", "bank", "sick"]:
    #         current_value = getattr(self, category) or 0
    #         setattr(self, category, current_value + minutes)

    def total(self) -> int:
        return self.work + self.holiday + self.bank + self.sick


class TimesheetDict(Attribute):

    attr_type = STRING
    _data = {}

    def __getitem__(self, key: date):
        return self._data[key]

    def __setitem__(self, key: date, value: Timesheet):
        self._data[key] = value

    def __iter__(self):
        yield from sorted(self._data.items())

    def serialize(self, value):
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

    def deserialize(self, value):
        data = loads(value)

        result: dict[date, Timesheet] = {}
        for week, values in data.items():
            key = date(int(week[1:5]),int(week[6:8]),int(week[9:11]))
            result[key] = Timesheet(
                work=values["work"],
                holiday=values["holiday"],
                bank=values["bank"],
                sick=values["sick"],
            )
        return result


class JobData(MapAttribute):
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
    """A DynamoDB User Table."""

    class Meta:
        table_name = "PyCalTimeUserData"
        region = AWS_DEFAULT_REGION

    id = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute()
    given_name = UnicodeAttribute()
    family_name = UnicodeAttribute()
    jobs = ListAttribute(of=JobData)

# if UserData.exists():
#     UserData.delete_table()

if not UserData.exists():
    UserData.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
