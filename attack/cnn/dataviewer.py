import matplotlib.pyplot as plt
import numpy as np

from regress import argparser, Regression

## Args + DB Info -----------------------------------

argparser.add_argument("-t", "--traces", type=int, default=[1], nargs="+", help="Trace to plot")
argparser.add_argument("-d", "--datasets", type=str, default=["a1u_tt:min"], nargs="+", help="Datasets to extract traces for plotting")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

datasets = {}
for dname in args.datasets:
    datasets[dname] = regression.datasets[dname]
regression.build_datasets(*list(datasets.values()))

fig, axs = plt.subplots(len(args.traces))
if len(args.traces) == 1: 
    axs = [axs]

## Main ---------------------------------------------

for label, ax in zip(args.traces, axs):
    ax.set_title(f"Trace {label}")

    for dname in datasets:
        info = datasets[dname].get_trace(label)
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
