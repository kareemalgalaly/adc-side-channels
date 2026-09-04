import sys
sys.path
sys.path.append('../../script')

import csvlib
import numpy as np

csv = csvlib.read("outputs/run_results.csv")
csv.add_computed_column(lambda a,p: (p-a) > 0.2,"Accuracy", "Peak Accuracy", name="Crashed")
csv.add_computed_column(lambda p,b: p > (0.4 if b == "_" else 0.8), "Peak Accuracy", "Bit", name="Learning")
csv.write_pivot(
    "outputs/pivot.csv",
    data = {
        "Test Accuracy" : np.average
        },
    filters = {
        "Crashed": lambda x: not x,
        "Learning": lambda x: x,
        "Bit": lambda x: x != "_"
        },
    cols = ["Bit"],
    rows = ["Dataset", "Test Dataset", "Network"]
    )

