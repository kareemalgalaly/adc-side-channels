import matplotlib.pyplot as plt
import numpy as np

from regress import argparser, Regression

argparser.add_argument("-t", "--traces", type=int, default=1, nargs="+", help="Trace to plot")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

d_lin = regression.datasets['linearized3k']
d_min = regression.datasets['sampled_min']
d_max = regression.datasets['sampled_max']
d_tru = regression.datasets['true_raw']

regression.build_datasets(d_lin, d_min, d_max, d_tru)

fig, axs = plt.subplots(len(args.traces))

for trace, ax in zip(args.traces, axs):

    lin_trace = d_lin.get_trace(trace)
    min_trace = d_min.get_trace(trace)
    max_trace = d_max.get_trace(trace)
    tru_trace = d_tru.get_trace(trace)

    time = np.linspace(0, tru_trace[0][-1], num=len(min_trace))
    lint = np.linspace(0, tru_trace[0][-1], num=len(lin_trace))

    ax.set_title(f"Trace {trace}")
    ax.plot(lint, lin_trace, alpha=0.5, label="lin", linestyle='solid')
    ax.plot(     *tru_trace, alpha=0.5, label="tru", linestyle='solid')
    ax.plot(time, min_trace, alpha=0.5, label="min", linestyle='dashed')
    ax.plot(time, max_trace, alpha=0.5, label="max", linestyle='dotted')
    ax.legend()

plt.show()
