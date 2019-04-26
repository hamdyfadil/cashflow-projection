import os

import pandas

from .constants import FILES, SHEETS

# Read in Configuration (useful global values)

#
# Initial conditions sheet
#
CONTROL = dict(map(lambda x: (x["KEY"], x["VALUE"]), pandas.read_excel(
    os.path.join(os.path.dirname(__file__), '..', FILES.CONTROL.value),
    sheet_name=SHEETS.INITIAL_CONDITIONS.value
).to_dict("records")))
