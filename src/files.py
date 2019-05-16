import tarfile
import os
from datetime import date as dt

import pandas

from .control import CONTROL
from .constants import FILES
from .aggregators import AGGREGATORS


def archive_state():
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


def output_to_excel(all_instances):
    output_columns = filter(
        lambda c: all(c in x for x in all_instances),
        ["DAY"] + ["NAME", "CLASS", "TO", "VALUE",
                   "AUTO", "NOTES"] + list(AGGREGATORS.keys())
    )

    pandas.DataFrame(all_instances).to_excel(
        FILES.OUTPUT.value,
        sheet_name="{}-month".format(CONTROL["GENERATE_MONTHS"]),
        columns=list(output_columns),
        index=False
    )
    archive_state()
