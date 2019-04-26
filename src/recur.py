from typing import Callable

import os
import math
from datetime import date as dt
from datetime import timedelta as td
from dateutil.relativedelta import relativedelta
from copy import deepcopy
from convertdate import hebrew

import pandas

from .constants import SHEETS, FILES
from .control import CONTROL


#
# Hebrew utilities
#
def to_heb_year_month_day(d):
    return hebrew.from_gregorian(d.year, d.month, d.day)


def hebrew_days(start, stop, holiday):
    holiday = tuple(map(int, map(str.strip, holiday.split(","))))

    def h(d):
        if to_heb_year_month_day(d)[1:] == holiday:
            return d

    return list(filter(
        lambda x: x,
        map(h, days_between(start, stop))
    ))

#
# Utilities
#
def days_between(start, stop, gap=td(days=1)):
    assert stop > start, "{} should be less than {}".format(stop, start)
    today = start
    while today < stop:
        yield today
        today = today + gap

#
# Recurrence Rules
#
class RecurrenceRule:
    def __init__(self, period, start, rule):
        self.period: td | relativedelta = period
        self.start: dt = start
        self.rule: Callable = rule

RECURRING_EVENTS_SHEETS = {
    SHEETS.YEARLY.value: RecurrenceRule(
        period=relativedelta(years=1),
        start=CONTROL["NOW"].to_pydatetime().date().replace(month=1, day=1),
        rule=lambda cs, ce, rr: rr["DATE"].to_pydatetime().date().replace(
            year=cs.year
        )
    ),
    SHEETS.MONTHLY.value: RecurrenceRule(
        period=relativedelta(months=1),
        start=CONTROL["NOW"].to_pydatetime().date().replace(day=1),
        rule=lambda cs, ce, rr: deepcopy(cs).replace(day=rr["DAY_OF_MONTH"])
    ),
    # FRIDAY Paycheck
    SHEETS.BIWEEKLY.value: RecurrenceRule(
        period=td(days=14),
        start=CONTROL["BIWEEKLY_START"].to_pydatetime().date(),
        rule=lambda cs, ce, rr: cs + td(rr["DAYS_AFTER_PAYCHECK_FRIDAY"])
    ),
    SHEETS.WEEKLY.value: RecurrenceRule(
        period=td(days=7),
        start=dt(2018, 4, 1),
        rule=lambda cs, ce, rr: cs + td(rr["DAYS_AFTER_SHABBAT"])
    ),
    SHEETS.ONE_TIME.value: RecurrenceRule(
        period=relativedelta(years=100),
        start=dt(2018, 1, 1),
        rule=lambda cs, ce, rr: rr["DATE"].to_pydatetime().date()
    ),
    SHEETS.YEARLY_HEBREW.value: RecurrenceRule(
        period=relativedelta(years=1),
        start=dt(2018, 1, 1),
        rule=lambda cs, ce, rr: hebrew_days(cs, ce, rr["HEBREW"])
    ),
}


def pull_recurring_events():
    df = pandas.read_excel(
        os.path.join(os.path.dirname(__file__), '..', FILES.CONTROL.value),
        sheet_name=list(RECURRING_EVENTS_SHEETS.keys())
    )
    for k, v in df.items():
        df[k] = v.to_dict("records")
        for r in df[k]:
            r["PATTERN"] = k

    return df


def interpret_timestamp(d):
    if (isinstance(d, float) and math.isnan(d)) or d is pandas.NaT:
        return None
    else:
        return d.to_pydatetime().date()


def generate_event_instances(start: dt, end: dt):
    """
    Inclusive
    """
    assert start < end
    instances = []
    for rec_pattern, recurrences in pull_recurring_events().items():
        cycle_period = RECURRING_EVENTS_SHEETS[rec_pattern].period
        cycle_start = RECURRING_EVENTS_SHEETS[rec_pattern].start
        cycle_day_rule = RECURRING_EVENTS_SHEETS[rec_pattern].rule

        # bring us to just before the period described
        while cycle_start + cycle_period <= start:
            cycle_start = cycle_start + cycle_period

        while cycle_start < end:
            cycle_end = cycle_start + cycle_period
            for recur in recurrences:
                days = cycle_day_rule(
                    cycle_start,
                    cycle_end,
                    recur
                )
                if not days:
                    continue

                if not isinstance(days, list):
                    days = [days]

                for day in days:
                    appendit = (
                        day <= end and
                        day >= start
                    )
                    start_day = interpret_timestamp(recur["START_DAY"])
                    end_day = interpret_timestamp(recur["END_DAY"])
                    if start_day:
                        appendit = appendit and day >= start_day
                    if end_day:
                        appendit = appendit and day <= end_day
                    if appendit:
                        r = deepcopy(recur)
                        r["DAY"] = day
                        instances.append(r)

            cycle_start = cycle_end

    instances.sort(key=lambda x: x["DAY"])
    return instances
