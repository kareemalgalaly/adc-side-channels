###############################################################################
# File        : trace_cacher.py
# Author      : kareemahmad
# Created     : 2025 Sep 08
# Description : Cache and potentially merge power trace datasets
###############################################################################

import os
import numpy as np
from classes import argparser, Regression

## Arguments -----------------------------------------------

argparser.add_argument("-D", "--datasets", type=str, nargs=2, help="Datasets to cache together")
args = argparser.parse_args()

try:
    os.mkdir(args.output)
except FileExistsError:
    pass

regression = Regression(args)
regression.load()

## Setup Datasets ------------------------------------------

datasets = {}
for dname in args.datasets:
    datasets[dname] = regression.datasets[dname]
regression.build_datasets(*list(datasets.values()))

## Generate Time Array -------------------------------------

info_0 = datasets[args.datasets[0]].get_trace(0, index=0)
time_arr = np.linspace(info_0.start, info_0.stop, len(info_0.trace), dtype=np.float32)

## Construct Files -----------------------------------------

seed = 0
pad  = 20
for label in range(256):
    try:
        info_list_0 = datasets[args.datasets[0]].get_trace(label, index=-1)
        info_list_1 = datasets[args.datasets[1]].get_trace(label, index=-1)
    except KeyError as e:
        print(f"WARNING: One or more datasets missing label {label}")
        continue

    for info_0 in info_list_0:
        for info_1 in info_list_1:
            with open(f"{args.output}/raw_s{seed}_{label}.txt", "w") as file:
                file.write(f"{'time'.ljust(pad)} {args.datasets[0].ljust(pad)} {args.datasets[0].ljust(pad)}\n")

                for t, i0, i1 in zip(time_arr, info_0.trace, info_1.trace):
                    file.write(f"{str(t).ljust(pad)} {str(i0).ljust(pad)} {str(i1).ljust(pad)}\n")

            seed += 1

