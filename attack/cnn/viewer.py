###############################################################################
# File        : /Users/kareemahmad/Projects/SideChannels/adc-side-channel/attack/cnn/viewer.py
# Author      : kareemahmad
# Created     : 
# Description : Plots traces.
#               See python viewer.py -h for usage instructions
###############################################################################


import matplotlib.pyplot as plt
import numpy as np

from classes import argparser, Regression

FIGX = 8
FIGY = 6

## Args + DB Info -----------------------------------

argparser.add_argument("-T", "--traces", type=int, default=[1], nargs="+", help="Trace to plot")
argparser.add_argument("-D", "--datasets", type=str, default=["a1u_tt:min"], nargs="+", help="Datasets to extract traces for plotting")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

datasets = {}
for dname in args.datasets:
    datasets[dname] = regression.datasets[dname]
regression.build_datasets(*list(datasets.values()))

fig, axs = plt.subplots(len(args.traces), figsize=(FIGX, FIGY))
if len(args.traces) == 1: 
    axs = [axs]

## Main ---------------------------------------------

for label, ax in zip(args.traces, axs):
    ax.set_title(f"Trace {label}")

    for dname in datasets:
        try:
            info = datasets[dname].get_trace(label)
        except KeyError as e:
            print(e)
            print("Listing all labels available")
            print(datasets[dname].builder.dataset.label_dict.keys())
            continue
        trace = info.trace
        start = info.start
        stop  = info.stop

        if datasets[dname].type == 'timed':
            time, trace = trace
        else:
            time = np.linspace(start, stop, num=len(trace))

        ax.plot(time, trace, alpha=0.5, label=dname, linestyle='solid')
    ax.legend()

plt.show()
