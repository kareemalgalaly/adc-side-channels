import matplotlib.pyplot as plt
import numpy as np
import argparse

from classes import argparser, Regression

FIGX = 8
FIGY = 6

## Args + DB Info -----------------------------------

argparser.add_argument("train_dataset", type=str, help="Training Trace Dataset")
argparser.add_argument("test_dataset",  type=str, help="Test Trace Dataset")
argparser.add_argument("test_trace",    type=int, default=-1, help="Test Trace index")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

## Datasets -----------------------------------------

train_dataset = regression.datasets[args.train_dataset]
test_dataset  = regression.datasets[args.test_dataset]
regression.build_datasets(train_dataset, test_dataset)

## Main ---------------------------------------------

if False:
    # For DPA I want to do 
    # get all traces with 1 as msb and avg
    # get all traces with 0 as msb and avg
    # take diff of my trace with the 1s and 0s

    zeros = []
    ones  = []

    for bit in range(8):
        s_0 = None
        s_1 = None

        for i in range(256):
            print(f"processing {bit} {i}/256", end="\r")
            trace, label = train_dataset.builder.datasets[bit][i]

            if label == 0:
                if s_0 is None: 
                    s_0 = trace
                else:
                    s_0 += trace
            else:
                if s_1 is None: 
                    s_1 = trace
                else:
                    s_1 += trace

        zeros.append(s_0 / 128)
        ones.append(s_1 / 128)

    print("\nplotting")

    fig, axs = plt.subplots(2, 4, figsize=(FIGX, FIGY))
    for i in range(8):
        x = i // 2
        y = i % 2
        axs[y, x].plot(np.abs(ones[i]-zeros[i]))
        axs[y, x].set_title(f"Difference of means: Bit {i}")

    plt.show()

def test_template(traces):
    correct = 0

    for trace in traces:

        test_trace, test_label = test_dataset.builder.dataset[trace]
        min_diff  = 1 << 31
        min_label = -1

        for i in range(256):
            print(f"processing {i}/256", end="\r")
            temp_trace, temp_label = train_dataset.builder.dataset[i]
            mlen = min(len(temp_trace), len(test_trace))
            diff = np.max(np.abs(test_trace[30:mlen] - temp_trace[30:mlen]))
            
            if diff < min_diff:
                min_label = temp_label
                min_diff  = diff

            # print(i, temp_label, diff, sep="\t")

        print(f"Test Trace:   {args.test_dataset}\t{test_label}\t  Best Match: {args.train_dataset}\t{min_label} ({min_diff})")
        if min_label == test_label: 
            correct += 1

    print(f"Accuracy {correct}/{len(traces)} = {100*correct/len(traces):2}%")

def test_template_bw(traces):
    correct_b = [0] * 8
    correct = 0
    zeros = []
    ones  = []

    mlen = min(len(train_dataset.builder.dataset[0][0]), len(test_dataset.builder.dataset[0][0]))
    print(mlen)

    for bit in range(8):
        s_0 = None
        s_1 = None

        for i in range(256):
            print(f"processing {bit} {i}/256", end="\r")
            trace, label = train_dataset.builder.datasets[bit][i]

            if label == 0:
                if s_0 is None: 
                    s_0 = trace
                else:
                    s_0 += trace
            else:
                if s_1 is None: 
                    s_1 = trace
                else:
                    s_1 += trace

        zeros.append((s_0 / 128)[20:mlen])
        ones.append((s_1 / 128)[20:mlen])

    for trace in traces:
        test_trace, test_label = test_dataset.builder.dataset[trace]

        test_label = int(test_label)
        pred_label = 0

        for bit in range(8):
            if np.max(np.abs(test_trace[20:mlen] - zeros[bit])) > np.max(np.abs(test_trace[20:mlen] - ones[bit])):
                pred_label |= 1 << bit
                correct_b[bit] += (test_label & (1 << bit)) != 0
            else:
                correct_b[bit] += (test_label & (1 << bit)) == 0

            # print(i, temp_label, diff, sep="\t")
        
        if (pred_label == test_label): correct += 1
        print(f"Test Trace:   {args.test_dataset}\t{test_label}\t{bin(test_label)}\t   Predicted Label:   {pred_label}\t{bin(pred_label)}")

    accs = "\n".join([f"Bit {i} : {correct_b[i]}/{len(traces)}\t{100*correct_b[i]/len(traces):2}%" for i in range(7, -1, -1)])
    print(f"Accuracy: \n{accs}\nCombined : {correct}/{len(traces)} {100*correct/len(traces):2}%")

if args.test_trace == -1:
    test_template_bw(range(256))
elif args.test_trace == -2:
    test_template(range(256))
else:
    test_template([args.test_trace])

