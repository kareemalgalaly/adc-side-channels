###############################################################################
# File        : adc-side-channel/attack/cnn/viewer.py
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
argparser.add_argument("-H", "--histogram", action="store_true", help="Plot histogram of data")
argparser.add_argument("-S", "--stack", action="store_true", help="Stack traces on same plot")
argparser.add_argument("-L", "--labels", nargs="+", default=[])
argparser.add_argument(      "--title", default=None)
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Plot Parameters ----------------------------------

plt.rcParams['figure.dpi'] = 300
plt.rcParams['figure.autolayout'] = True

## Datasets -----------------------------------------

datasets = {}
try:
    for dname in args.datasets:
        datasets[dname] = regression.datasets[dname]
except KeyError:
    print("Available Datasets:")
    print(*regression.datasets.keys())
    exit(1)
regression.build_datasets(*list(datasets.values()))

if args.stack:
    fig, axs = plt.subplots(1, figsize=(FIGX, FIGY))
    axs = [axs] * len(args.traces)
else:
    fig, axs = plt.subplots(len(args.traces), figsize=(FIGX, FIGY))
    if len(args.traces) == 1: 
        axs = [axs]

## Main ---------------------------------------------

for label, ax in zip(args.traces, axs):
    if not args.histogram:
        ax.set_title(f"Trace {label}")
        ax.set_xlabel("Time (us)")
        ax.set_ylabel("Normalized Power")

    if args.title:
        ax.set_title(args.title)

    for dname in datasets:
        try:
            if label != -1:
                label = label % 256
                index = label // 256
            else:
                index = 0
            info = datasets[dname].get_trace(label, index)
        except KeyError as e:
            print(e)
            print("Listing all labels available")
            print(datasets[dname].builder.dataset.label_dict.keys())
            continue
        trace = info.trace
        start = info.start
        stop  = info.stop

        time = None
        if datasets[dname].type == 'timed':
            time, trace = trace
    
        if args.labels: 
            lbl = args.labels.pop(0)
        else:
            lbl = f"{dname}[{label}]"

        if args.histogram:
            if datasets[dname].cols == 1:
                ax.hist(trace, bins=50, histtype='step', label=lbl)
                print(f"{dname}[{label}]", min(trace), max(trace))
            else:
                for c, trace_i in enumerate(trace): 
                    ax.hist(trace_i, bins=50, histtype='step', label=f"{lbl}.{c}")
                    print(f"{dname}.{c}[{label}] ({lbl})", min(trace_i), max(trace_i))
        else:
            if datasets[dname].cols == 1:
                if time is None:
                    time = np.linspace(start, stop, num=len(trace))
                ax.plot(time, trace, alpha=0.5, label=lbl, linestyle='solid')
                print(f"{lbl}\t[{trace.min():7.3} : {trace.max():7.3}]")
            else:
                if time is None:
                    print(type(start), type(stop))
                    time = np.linspace(start, stop, num=trace.shape[1])
                for i, trace_i in enumerate(trace):
                    print(i, trace_i)
                    ax.plot(time, trace_i, alpha=0.5, label=f"{lbl}[{i}]", linestyle='solid')

    if not args.stack: ax.legend()

if args.stack: ax.legend()
try:
    plt.show()
except KeyboardInterrupt:
    print("Exiting")
