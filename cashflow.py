# finance.py
from datetime import date as dt
from datetime import timedelta as td
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from copy import deepcopy
import math

# from matplotlib import pyplot as plt
import pandas
from convertdate import hebrew


#
# Hebrew
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


def days_between(start, stop, gap=td(days=1)):
    assert stop > start, "{} should be less than {}".format(stop, start)
    today = start
    while today < stop:
        yield today
        today = today + gap


#
# Handling columns
#

CARRY_OVER_COLUMNS = ["NAME", "CLASS", "TO", "VALUE", "AUTO", "NOTES"]

FILES = {
    "CONTROL": "CONTROL.xlsx",
    "OUTPUT": "OUTPUT.xlsx"
}

CONTROL = dict(map(lambda x: (x["KEY"], x["VALUE"]), pandas.read_excel(
    FILES["CONTROL"],
    sheet_name="INITIAL_CONDITIONS"
).to_dict("records")))

RECURRING_EVENTS_SHEETS = {
    "YEARLY": dict(
        period=relativedelta(years=1),
        start=CONTROL["NOW"].to_pydatetime().date().replace(month=1, day=1),
        rule=lambda cs, ce, rr: rr["DATE"].to_pydatetime().date().replace(
            year=cs.year
        )
    ),
    "MONTHLY": dict(
        period=relativedelta(months=1),
        start=CONTROL["NOW"].to_pydatetime().date().replace(day=1),
        rule=lambda cs, ce, rr: deepcopy(cs).replace(day=rr["DAY_OF_MONTH"])
    ),
    # FRIDAY Paycheck
    "BIWEEKLY": dict(
        period=td(days=14),
        start=CONTROL["BIWEEKLY_START"].to_pydatetime().date(),
        rule=lambda cs, ce, rr: cs + td(rr["DAYS_AFTER_PAYCHECK_FRIDAY"])
    ),
    "WEEKLY": dict(
        period=td(days=7),
        start=dt(2018, 4, 1),
        rule=lambda cs, ce, rr: cs + td(rr["DAYS_AFTER_SHABBAT"])
    ),
    "ONE-TIME": dict(
        period=relativedelta(years=100),
        start=dt(2018, 1, 1),
        rule=lambda cs, ce, rr: rr["DATE"].to_pydatetime().date()
    ),
    "YEARLY-HEBREW": dict(
        period=relativedelta(years=1),
        start=dt(2018, 1, 1),
        rule=lambda cs, ce, rr: hebrew_days(cs, ce, rr["HEBREW"])
    ),
}
AGGREGATORS = OrderedDict([
    # Negative Cashflow
    ("EXPENSES", {
        "aggregation_rule": lambda a, x: a + min(0, x),
        "initial_value": 0
    }),
    # Positive Cashflow
    ("INCOME", {
        "aggregation_rule": lambda a, x: a + max(0, x),
        "initial_value": 0
    }),
    # Difference of Cashflows
    ("BALANCE", {
        "aggregation_rule": lambda a, x: a + x,
        "initial_value": CONTROL["CURRENT"]
    }),
    # More complicated calculation, to be done later.
    ("WIGGLE", {
        "aggregation_rule": lambda a, x: a,
        "initial_value": 0
    }),
    ("LATENT", {
        "aggregation_rule": lambda a, x: a,
        "initial_value": 0
    }),
    ("LEAD", {
        "aggregation_rule": lambda a, x: a,
        "initial_value": 0
    }),
])


def pull_recurring_events():
    df = pandas.read_excel(
        FILES["CONTROL"],
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


def generate_event_instances(start, end):
    """
    Inclusive
    """
    assert start < end
    instances = []
    for rec_pattern, recurrences in pull_recurring_events().items():
        cycle_period = RECURRING_EVENTS_SHEETS[rec_pattern]["period"]
        cycle_start = RECURRING_EVENTS_SHEETS[rec_pattern]["start"]
        cycle_day_rule = RECURRING_EVENTS_SHEETS[rec_pattern]["rule"]

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


def set_aggregates(instances, current_value_key="VALUE"):
    aggregate = dict(((k, v["initial_value"]) for k, v in AGGREGATORS.items()))
    for i in instances:
        current_value = i[current_value_key]
        for metric, prev_value in aggregate.items():
            new_value = AGGREGATORS[metric]["aggregation_rule"](
                prev_value, current_value
            )
            aggregate[metric] = new_value
            i[metric] = new_value
    return aggregate


def graph_aggregates(instances):
    pass
    # for metric in AGGREGATORS.keys():
    #     plt.plot(map(lambda x: x[metric], instances))
    #     plt.title(metric)
    #     plt.savefig("{}.png".format(metric))
    #     plt.clf()


def archive_state():
    import tarfile
    import os
    here = "."
    archive = os.path.join(
        here, "..", "PAST_STATES", dt.today().strftime("%Y-%m-%d.tar")
    )
    t = tarfile.open(
        archive,
        mode="w:gz"
    )
    t.add(here)
    t.close()


def calculate_wiggle(instances):
    expense_segments = []
    cur = []

    def add_es(es):
        if es:
            val = min((x["BALANCE"] for x in es))
            for c in es:
                c["WIGGLE"] = val - CONTROL["SET_ASIDE"]
            expense_segments.append(es)

    for i in instances:
        cur.append(i)
        if i["VALUE"] > 0:
            add_es(cur)
            cur = []
    add_es(cur) if cur else None

    lowest = expense_segments[-1][0]["WIGGLE"]  # initial value
    for es in reversed(expense_segments):
        lowest = min(lowest, es[0]["WIGGLE"])
        for e in es:
            e["WIGGLE"] = lowest


def calculate_latent_production(instances, day_dif=14):
    i = 0
    j = 0
    while i < len(instances):
        in_i = instances[i]
        d_i = in_i["DAY"]
        while (instances[j]["DAY"] - d_i).days < day_dif:
            if j >= len(instances) - 1:
                break
            else:
                j += 1

        if i == j:
            in_i["LATENT"] = in_i["BALANCE"] - CONTROL["SET_ASIDE"]
        else:
            in_i["LATENT"] = min(map(
                lambda x: x["BALANCE"],
                instances[i:j]
            )) - CONTROL["SET_ASIDE"]
        i += 1


def calculate_lead_time(instances):
    for i in range(len(instances)):
        in_i = instances[i]
        for j in instances[i:]:
            if j["LATENT"] < in_i["LATENT"]:
                in_i["LEAD"] = (j["DAY"] - in_i["DAY"]).days
                break
        if "LEAD" not in in_i:
            in_i["LEAD"] = "PRODUCTION"


def chart_expense_shares(final_aggregate_states):
    pass
    # # Make expenses shares
    # sizes, labels = [], []
    # for pool, agg_state in filter(
    #     lambda x: x[0] != "ALL" and x[1]["EXPENSES"] < 0,
    #     final_aggregate_states.items()
    # ):
    #     sizes.append(abs(agg_state["EXPENSES"]))
    #     labels.append(pool)
    # fig1, ax1 = plt.subplots()
    # ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    # ax1.axis('equal')
    # plt.savefig("expenses.png")

    # # Make allocation graph
    # income = sum(map(
    #     lambda agg_state: agg_state[1]["INCOME"],
    #     filter(
    #         lambda x: x[0] != "ALL" and x[1]["INCOME"] > 0,
    #         final_aggregate_states.items()
    #     )
    # ))
    # sizes.append(income - sum(sizes))
    # labels.append("Unspent Income")
    # fig1, ax1 = plt.subplots()
    # ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    # ax1.axis('equal')
    # plt.savefig("allocation.png")


def get_months(field):
    return int(field)


def format_money(money):
    return "${:,.2f}".format(money)


if __name__ == "__main__":
    month_projection = get_months(CONTROL["GENERATE_MONTHS"])

    all_instances = list(generate_event_instances(
        CONTROL["NOW"].to_pydatetime().date(),
        CONTROL["NOW"].to_pydatetime().date() + relativedelta(
            months=month_projection
        )
    ))

    pools = OrderedDict([
        ("ALL", lambda p, x: True)] + [
        (c, lambda p, x: x["CLASS"] == p) for c in sorted(set(
            (x["CLASS"] for x in all_instances)
        ))
    ])

    pool_instances = dict((
        (pool, deepcopy(list(filter(
            lambda x: criteria(pool, x), all_instances
        )))) for pool, criteria in pools.items()
    ))

    final_aggregate_states = {}
    for pool, instances in pool_instances.items():
        final_aggregate_states[pool] = set_aggregates(instances)

        if pool == "ALL":
            calculate_wiggle(instances)

        columns = ["DAY"] + CARRY_OVER_COLUMNS + list(AGGREGATORS.keys())
        columns = filter(lambda c: all(c in x for x in instances), columns)

    # Fill in aggregates for each instance
    set_aggregates(all_instances)
    calculate_wiggle(all_instances)
    calculate_latent_production(all_instances)
    calculate_lead_time(all_instances)

    print("Spare Capital", format_money(all_instances[0]["WIGGLE"]))

    pandas.DataFrame(all_instances).to_excel(
        FILES["OUTPUT"],
        sheet_name="{}-month".format(month_projection),
        columns=list(columns),
        index=False
    )

    #
    # Print useful information
    #
    print("Disposable Income above allocation")
    wiggle_values = set()
    prev_day = None
    for x in all_instances:
        w = x["WIGGLE"]
        if w not in wiggle_values:
            wiggle_values.add(w)
            print(
                x["DAY"],
                format_money(x["WIGGLE"]),
                "({0} days later)".format(
                    (x["DAY"] - prev_day).days
                ) if prev_day else ""
            )
            prev_day = x["DAY"]

    archive_state()
