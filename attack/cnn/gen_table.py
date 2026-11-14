#!/usr/bin/env python

import sys
sys.path
sys.path.append('../../script')

import time
import csvlib
import numpy as np

import argparse
argparser = argparse.ArgumentParser(prog="gen_table")
argparser.add_argument("-i", "--input",  type=str, default="outputs/run_results.csv", help="Input CSV File")
argparser.add_argument("-o", "--output", type=str, default="outputs/pivot.csv",       help="Output CSV File")
argparser.add_argument("-a", "--age",    type=int, default=10*365*24*3600,            help="Age limit in seconds (default 10 years)")
args = argparser.parse_args()

csv = csvlib.read(args.input)
csv.add_computed_column(lambda a,p: (p-a) > 0.2,"Accuracy", "Peak Accuracy", name="Crashed")
csv.add_computed_column(lambda p,b: p > (0.4 if b == "_" else 0.72), "Peak Accuracy", "Bit", name="Learning")
csv.add_computed_column(lambda a: time.strptime(a, "%y%m%d_%H%M") < time.localtime(time.time() - args.age), "Job Timestamp", name="Expired")

# table = csv.pivot(
csv.write_pivot(
    args.output,
    data = [
        ("Test Accuracy (avg)", "Test Accuracy", np.average),
        ("Test Accuracy (std)", "Test Accuracy", np.std),
        ("Count"              , "Seed",          len)
        ],
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
