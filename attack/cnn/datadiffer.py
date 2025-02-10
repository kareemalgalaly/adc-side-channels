import matplotlib.pyplot as plt
import numpy as np

from regress import argparser, Regression

## Args + DB Info -----------------------------------

argparser.add_argument("dataset1", type=str, help="First Trace Dataset")
argparser.add_argument("trace1",   type=int, help="First Trace Label")
argparser.add_argument("dataset2", type=str, help="Second Trace Dataset")
argparser.add_argument("trace2",   type=int, help="Second Trace Label")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

dataset1 = regression.datasets[args.dataset1]
dataset2 = regression.datasets[args.dataset2]
regression.build_datasets(dataset1, dataset2)

#print(dataset1.builder.dataset.label_dict)
#exit()

fig, ax = plt.subplots(1)

## Main ---------------------------------------------

ax.set_title(f"Diff {args.dataset1}[{args.trace1}]-{args.dataset2}[{args.trace2}]")

info1  = dataset1.get_trace(args.trace1)
trace1, start, stop = info1
trace2 = dataset2.get_trace(args.trace2).trace

if len(trace1) != len(trace2):
    print("Traces do not have equal length")

time = np.linspace(start, stop, num=len(trace1))
ax.plot(time, trace1-trace2, alpha=0.5, linestyle='solid')

plt.show()

