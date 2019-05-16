from datetime import date
from dateutil.relativedelta import relativedelta

from src.control import CONTROL
from src.generate_instances import get_instances_up_to, get_production_instances


def format_money(money):
    return "${:,.2f}".format(money)


def lump(p, days, i):
    return p * (1 + i) ** (days / 365.)


def projection(all_instances, goal_date, interest_rate=0.0, four_oh_one_k_returns=0.12):
    projection_value = 0
    now = CONTROL["NOW"].date()

    # Current 401k balance
    projection_value += lump(CONTROL["401K_BALANCE"],
                             (goal_date - now).days, four_oh_one_k_returns)
    # Current production balance
    projection_value += lump(CONTROL["PRODUCTION_ASSETS"],
                             (goal_date - now).days, interest_rate)
    # Current static assets
    projection_value += CONTROL["STATIC_ASSETS"]

    # 401k contribution + returns
    # (a mathematical annuity)
    contribution = CONTROL["BIWEEKLY_GROSS_PAY"] * \
        CONTROL["401K_EFFECTIVE_CONTRIBUTION_PERCENT"]
    paychecks = (goal_date - now).days // 14
    for i in range(paychecks):
        effective_now = now + (i * relativedelta(weeks=2))
        sit = goal_date - effective_now
        projection_value += contribution * \
            ((1 + four_oh_one_k_returns) ** (sit.days / 365.))

    # Production + interest
    prev_value = 0
    for p in filter(
        lambda x: x["WIGGLE"] >= 0.,
        get_production_instances(all_instances)
    ):
        gain = p["WIGGLE"] - prev_value
        sit = goal_date - p["DAY"]
        projection_value += gain * ((1 + interest_rate) ** (sit.days / 365.))
        prev_value = p["WIGGLE"]

    return projection_value


if __name__ == "__main__":
    """
    Calculate progress to goals
    """
    goal_value = CONTROL["GOAL_VALUE"]
    goal_date = CONTROL["GOAL_DATE"].date()

    def summarize_projection(value):
        return "{} ({:,.1f}%)".format(
            format_money(value),
            100 * value / goal_value,
        )

    # So wiggle values are worked out properly, we project a little further,
    # then prune out transactions beyond the target
    all_instances = get_instances_up_to(goal_date + relativedelta(months=1))
    all_instances = list(filter(lambda i: i["DAY"] < goal_date, all_instances))

    ljust = 50
    print("Base Production + 401k:".ljust(ljust), summarize_projection(
        projection(all_instances, goal_date, interest_rate=0.0)
    ))

    print("Ramsey projection (production yield 12%):".ljust(ljust), summarize_projection(
        projection(all_instances, goal_date, interest_rate=0.12)
    ))

    print("Good projection (production yield 100%):".ljust(ljust), summarize_projection(
        projection(all_instances, goal_date, interest_rate=1.00)
    ))
