from typing import Set

import math

from src.control import CONTROL
from src.generate_instances import get_production_instances


def format_money(money):
    return "${:,.2f}".format(money)


if __name__ == "__main__":
    """
    Print production dates and values
    """
    prev_day = CONTROL["NOW"].date()
    for x in get_production_instances():
        print(
            x["DAY"],
            format_money(x["WIGGLE"]),
            "({0} days later)".format(
                (x["DAY"] - prev_day).days
            )
        )
        prev_day = x["DAY"]
