#!/usr/bin/env python

import sys
sys.path
sys.path.append('../../script')

import time
import csvlib
import numpy as np

AGE = 1 * 3600

csv = csvlib.read("outputs/run_results.csv")
csv.add_computed_column(lambda a,p: (p-a) > 0.2,"Accuracy", "Peak Accuracy", name="Crashed")
csv.add_computed_column(lambda p,b: p > (0.4 if b == "_" else 0.8), "Peak Accuracy", "Bit", name="Learning")
csv.add_computed_column(lambda a: time.strptime(a, "%y%m%d_%H%M") < time.localtime(time.time() - AGE), "Job Timestamp", name="Expired")
# table = csv.pivot(
csv.write_pivot(
    "outputs/pivot.csv",
    data = {
        "Test Accuracy" : np.average
        },
    filters = {
        "Expired": lambda x: not x,
        "Crashed": lambda x: not x,
        "Learning": lambda x: x,
        "Bit": lambda x: x != "_"
        },
    cols = ["Bit"],
    rows = ["Dataset", "Test Dataset", "Network"]
    )

# print(table)
