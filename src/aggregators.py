from collections import OrderedDict

from .control import CONTROL

AGGREGATORS = OrderedDict([
    # # Negative Cashflow
    # ("EXPENSES", {
    #     "aggregation_rule": lambda a, x: a + min(0, x),
    #     "initial_value": 0
    # }),
    # # Positive Cashflow
    # ("INCOME", {
    #     "aggregation_rule": lambda a, x: a + max(0, x),
    #     "initial_value": 0
    # }),
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

    # pools = OrderedDict([
    #     ("ALL", lambda p, x: True)] + [
    #     (c, lambda p, x: x["CLASS"] == p) for c in sorted(set(
    #         (x["CLASS"] for x in all_instances)
    #     ))
    # ])

    # pool_instances = dict((
    #     (pool, deepcopy(list(filter(
    #         lambda x: criteria(pool, x), all_instances
    #     )))) for pool, criteria in pools.items()
    # ))

    # final_aggregate_states = {}
    # for pool, instances in pool_instances.items():
    #     final_aggregate_states[pool] = set_aggregates(instances)

    #     if pool == "ALL":
    #         calculate_wiggle(instances)


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
    """
    Must be run after `calculate_latent_production`
    """
    for i in range(len(instances)):
        in_i = instances[i]
        for j in instances[i:]:
            if j["LATENT"] < in_i["LATENT"]:
                in_i["LEAD"] = (j["DAY"] - in_i["DAY"]).days
                break
        if "LEAD" not in in_i:
            in_i["LEAD"] = "PRODUCTION"
