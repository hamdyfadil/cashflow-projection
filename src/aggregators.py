from collections import OrderedDict

from .control import CONTROL

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
