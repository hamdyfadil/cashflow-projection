from typing import Set

from datetime import date as dt
from datetime import timedelta as td
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from copy import deepcopy
import math

# from matplotlib import pyplot as plt
import pandas

from src.control import CONTROL
from src.constants import FILES
from src.aggregators import AGGREGATORS, set_aggregates
from src.recur import generate_event_instances


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

        columns = filter(
            lambda c: all(c in x for x in instances),
            ["DAY"] + ["NAME", "CLASS", "TO", "VALUE",
                       "AUTO", "NOTES"] + list(AGGREGATORS.keys())
        )

    # Fill in aggregates for each instance
    set_aggregates(all_instances)
    calculate_wiggle(all_instances)
    calculate_latent_production(all_instances)
    calculate_lead_time(all_instances)

    print("Spare Capital", format_money(all_instances[0]["WIGGLE"]))

    pandas.DataFrame(all_instances).to_excel(
        FILES.OUTPUT.value,
        sheet_name="{}-month".format(month_projection),
        columns=list(columns),
        index=False
    )

    #
    # Print useful information
    #
    print("Disposable Income above allocation")
    wiggle_values: Set[float] = set()
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
