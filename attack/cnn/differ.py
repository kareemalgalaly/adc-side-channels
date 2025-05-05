import matplotlib.pyplot as plt
import argparse
import numpy as np

from classes import argparser, Regression

FIGX = 8
FIGY = 6

## Args + DB Info -----------------------------------

argparser.add_argument("dataset1", type=str, help="First Trace Dataset")
argparser.add_argument("trace1",   type=int, help="First Trace Label")
argparser.add_argument("dataset2", type=str, help="Second Trace Dataset")
argparser.add_argument("trace2",   type=int, help="Second Trace Label")
argparser.add_argument("prompt", nargs=argparse.REMAINDER, help="Additional diff pairs")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

traces   = [args.trace1, args.trace2]
datasets = [regression.datasets[args.dataset1], regression.datasets[args.dataset2]]

assert (len(args.prompt) % 4) == 0, "Additional arguments must be divisible by 4"
for i in range(0, len(args.prompt), 4):
    datasets.append(regression.datasets[args.prompt[i+0]])
    datasets.append(regression.datasets[args.prompt[i+2]])
    traces.append(int(args.prompt[i+1]))
    traces.append(int(args.prompt[i+3]))

regression.build_datasets(*datasets)

#print(dataset1.builder.dataset.label_dict)
#exit()

fig, ax = plt.subplots(1, figsize=(FIGX, FIGY))

## Main ---------------------------------------------

ax.set_title("Differential Power Traces")
#f"Diff {args.dataset1}[{args.trace1}]-{args.dataset2}[{args.trace2 if args.trace2 != -1 else 'avg'}]")

for i in range(0, len(datasets), 2):
    dataset1 = datasets[i]
    dataset2 = datasets[i+1]
    info1  = dataset1.get_trace(traces[i])
    trace1, start, stop = info1
    trace2 = dataset2.get_trace(traces[i+1]).trace

    if len(trace1) != len(trace2):
        print("Traces do not have equal length")
        mlen = min(len(trace1), len(trace2))
        trace1 = trace1[:mlen]
        trace2 = trace2[:mlen]

    time = np.linspace(start, stop, num=len(trace1))
    ax.plot(time, trace1-trace2, alpha=0.5, linestyle='solid', label=f"{dataset1.name[:-4]}[{traces[i]}]-{dataset2.name[:-4]}[{traces[i+1] if traces[i+1] != -1 else 'avg'}]")
#f"Diff {args.dataset1}[{args.trace1}]-{args.dataset2}[{args.trace2 if args.trace2 != -1 else 'avg'}]")

ax.legend()
plt.show()

