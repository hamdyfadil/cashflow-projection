from typing import Set

from dateutil.relativedelta import relativedelta

from src.control import CONTROL
from src.recur import generate_event_instances
from src.aggregators import set_aggregates, calculate_wiggle, calculate_latent_production, calculate_lead_time


def get_months(field):
    return int(field)


def get_instances_up_to(end=None):
    """
    Returns all projected transactions, sorted by date, with aggregations calculated and set.

    end: Date, defaults to months after start configured in control
    Start: Date given in control spreadsheet
    """
    start = CONTROL["NOW"].to_pydatetime().date()
    if end is None:
        end = start + relativedelta(
            months=get_months(CONTROL["GENERATE_MONTHS"])
        )
    all_instances = list(generate_event_instances(start, end))

    set_aggregates(all_instances)
    calculate_wiggle(all_instances)
    calculate_latent_production(all_instances)
    calculate_lead_time(all_instances)

    return all_instances


def get_production_instances(all_instances=None):
    """
    Returns instances where WIGGLE has increased.
    (helpful if you're working with the area underneath the production curve)
    """
    if all_instances is None:
        all_instances = get_instances_up_to()

    production_instances = []

    wiggle_values: Set[float] = set()
    for x in all_instances:
        w = x["WIGGLE"]
        if w not in wiggle_values:
            wiggle_values.add(w)
            production_instances.append(x)

    return production_instances
