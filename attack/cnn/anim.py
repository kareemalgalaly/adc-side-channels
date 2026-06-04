###############################################################################
# File        : adc-side-channel/attack/cnn/anim.py
# Author      : kareemahmad
# Created     : 
# Description : 
###############################################################################


import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

from classes import argparser, Regression

FIGX = 8
FIGY = 6

## Args + DB Info -----------------------------------

argparser.add_argument("-D", "--datasets", type=str, default=["a1u_tt:min"], nargs="+", help="Datasets to extract traces for plotting")
argparser.add_argument(      "--stack", action="store_true", help="Stack traces on same plot")
argparser.add_argument("-C", "--maxcount", type=int, default=None, help="Limit number of subseeds plotted")
argparser.add_argument("-F", "--frameinterval", type=int, default=30, help="Frame interval")
argparser.add_argument("-S", "--start", type=int, default=0, help="Start animation")

args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

is_tru = False
datasets = {}
try:
    for dname in args.datasets:
        datasets[dname] = regression.datasets[dname]
        is_tru = datasets[dname].type == "timed"
except KeyError:
    print("Available Datasets:")
    print(*regression.datasets.keys())
    exit(1)
regression.build_datasets(*list(datasets.values()))

if args.stack:
    fig, axs = plt.subplots(1, figsize=(FIGX, FIGY))
    axs = [axs] * len(args.datasets)
else:
    fig, axs = plt.subplots(len(args.datasets), figsize=(FIGX, FIGY))
    if len(args.datasets) == 1: 
        axs = [axs]

## Construct Anim Data ------------------------------

labl = []
data = []
mrptcnt = 0
# mtracel = 0
yrng = []

for n, d in datasets.items():
    labl.append(n)
    ddata = []
    data.append(ddata)
    dlen = 0
    ymin = 0
    ymax = 0

    for label in range(args.start, 256):
        ddata_i = [di.trace for di in d.get_trace(label, -1)]
        ddata.append(ddata_i)
        mrptcnt = max(mrptcnt, len(ddata_i))
        if is_tru:
            ymax = max(ymax, max([max(di[1]) for di in ddata_i]))
            ymin = min(ymin, min([min(di[1]) for di in ddata_i]))
        else:
            ymax = max(ymax, max([max(di) for di in ddata_i]))
            ymin = min(ymin, min([min(di) for di in ddata_i]))

    yrng.append((ymin, ymax))

if args.maxcount: mrptcnt = min(mrptcnt, args.maxcount)
numfram = mrptcnt * 256

## Initial Plot -------------------------------------

lines = []
lgnds = []

for i in range(len(args.datasets)):
    l = labl[i]
    d = data[i][0][0]
    a = axs[i]
    if is_tru:
        lines.append(a.plot(d[0], d[1], label=l)[0])
    else:
        t = np.linspace(0, 1, len(d))
        lines.append(a.plot(t, d, label=l)[0])

for ax, rng in zip(axs, yrng):
    lgnds.append(ax.legend(loc=1))
    ax.set(ylim=rng)

def update(frame):
    frame += args.start
    fmaj = frame // mrptcnt
    fmin = frame  % mrptcnt

    for i in range(len(args.datasets)):
        d = data[i][fmaj]
        if fmin >= len(d): 
            dii = d[-1]
        else:
            dii = d[fmin]

        if is_tru:
            lines[i].set_xdata(dii[0])
            lines[i].set_ydata(dii[1])
        else:
            lines[i].set_ydata(dii)

        t = lgnds[0].get_texts()[i] if args.stack else lgnds[i].get_texts()[0]
        t.set_text(f"{labl[i]}[{fmaj}:{fmin}]]")
            
    return lines

print(numfram)
ani = animation.FuncAnimation(fig=fig, func=update, frames=numfram-args.start, interval=args.frameinterval)

try:
    plt.show()
except KeyboardInterrupt:
    print("Exiting")
