###############################################################################
# File        : attack/cnn/subsampler.py
# Author      : kareemahmad
# Created     : 
# Description : Subsample ngspice output file to csv 
###############################################################################

import numpy as np
import matplotlib.pyplot as plt

def select_func_gen(mode):
    def bmin(t1, v1, t2, v2, t): return v1
    def bmax(t1, v1, t2, v2, t): return v2
    def vmin(t1, v1, t2, v2, t): return min(v1, v2)
    def vmax(t1, v1, t2, v2, t): return max(v1, v2)
    def near(t1, v1, t2, v2, t): return v1 if t - t1 > t2 - t else v2
    def mlin(t1, v1, t2, v2, t): return (t-t1)/(t2-t1) * (v2-v1) + v1

    if mode == "BMIN": return bmin
    elif mode == "BMAX": return bmax
    elif mode == "VMIN": return vmin
    elif mode == "VMAX": return vmax
    elif mode == "NEAREST": return near
    elif mode == "LINEAR": return mlin
    else: raise ValueError("Illegal mode selected")

def sample_func_gen(mode):
    if   mode == 'MIN': return lambda x: np.min(x)
    elif mode == 'MAX': return lambda x: np.max(x)
    elif mode == 'AVG': return lambda x: np.average(x)
    else: raise ValueError("Illegal mode selected")

def sample_file(fpath, sample_interval, max_samples, sample_mode="AVG", column=0):
    time_col = column << 1
    valu_col = time_col + 1

    f = sample_func_gen(sample_mode)
    l = select_func_gen('LINEAR')

    with open(fpath, 'r') as file:
        header = file.readline()

        val_arr = []
        val_win = []

        stim, value = file.readline().strip().split()
        stim = float(stim)
        value = float(value)
        ptim = stim
        wtim = stim + sample_interval
        val_win.append(value)

        for line in file.readlines():
            if len(val_arr) == max_samples: break
            stim, value = line.strip().split()
            stim = float(stim)
            value = float(value)

            if stim >= wtim:
                val_arr.append(f(val_win))

                # if time is too big a gap:
                wtim += sample_interval
                while stim > wtim:
                    val_arr.append(l(ptim, val_arr[-1], stim, value, (len(val_arr)+0.5)*sample_interval))
                    wtim += sample_interval

                val_win = [value]

            else:
                val_win.append(value)

            ptim = stim

        return val_arr

def do_parse(file_in, file_out, interval=1e-6, samples=1000, time=2.5e-4, index=0, sample_mode="LINEAR"):
    col_t = index << 1
    col_v = col_t + 1

    # time_index = total number of intervals in resulting output
    time_index = int(time / interval)
    # print(time_index)

    # time = np array with even intervals within provided time
    time = np.linspace(0, time, num=time_index, endpoint=False)
    # print(time)
    # vals = np array with time_index number of zeroes
    vals = np.zeros((time_index,))
    # print(len(vals))
    # interp = select_func_gen(sample_mode)

    with open(file_in, "r") as file:
        # output file line
        l = file.readline().strip().split(",")
        sample_counter = 0
        curr_index = 0

        # initialize time and val with value of first output line
        # it should be zero, zero
        tp = float(l[col_t])
        vp = float(l[col_v])
        time[curr_index] = tp
        vals[curr_index] = vp

        for line in file.readlines():
            # If we counted the full number of samples, stop reading
            if sample_counter == samples:
                break
            
            # tp, vp = time and val from line
            l = line.strip().split(",")
            tp = float(l[col_t])
            vp = float(l[col_v])

            # First, check if the next time value is smaller than tp
            # No need for approximation, just add
            if tp <= time[curr_index+1]:
                curr_index += 1
                vals[curr_index] = vp
            else:
                # count number of time intervals NOT specified in input file
                counter = 0
                temp = curr_index
                prev_val = vals[curr_index]

                # while next time value is smaller than tp, increment counter
                # if same, still increment
                while temp < time_index - 1 and time[temp+1] <= tp:
                    counter += 1
                    temp += 1

                print(counter)
                print(temp)
                
                # now store values of linear approximation
                # if counter = 0 or 1, means we have no empty intervals, so no need to approximate
                if counter != (0 or 1):
                    print((vp - prev_val) / counter)
                    for i in range(counter):
                        vals[curr_index + 1] = prev_val + (vp - prev_val) / counter * i
                        curr_index += 1

                # Store the current time and value
                time[curr_index] = tp
                vals[curr_index] = vp
                curr_index += 1
                sample_counter += 1
            
    with open(file_out, "w") as file:
        for t, v in zip(time, vals):
            file.write(f"{t},{v}\n")

if __name__ == "__main__":#
    import argparse

    argparser = argparse.ArgumentParser(prog="subsampler.py", description="Subsample raw ngspice output to csv")
    argparser.add_argument("inputfile", type=str, help="Raw ngspice output data file to read")
    argparser.add_argument("outputfile", type=str, help="Target output csv file to write")
    argparser.add_argument("-i", "--interval", type=float, default=1e-9, help="Subsampling interval size")
    argparser.add_argument("-s", "--samples", type=int, default=12275, help="Number of samples of inputfile")
    argparser.add_argument("-t", "--time", type=float, default=2.5e-4, help="Total length of time of inputfile")
    argparser.add_argument("-c", "--column", type=int, default=0, help="Column index of data to read from inputfile. Ignores time columns: 0 = first data column, 1 = second data column, etc.")
    argparser.add_argument("-m", "--mode", type=str, default="LINEAR", help="Subsampling mode: BMIN/BMAX use value at min/max bounding sample, VMIN/VMAX use min/max value of bounding samples, NEAREST use value from nearest sample, LINEAR linearly interpolate between samples")

    args = argparser.parse_args()
    do_parse(args.inputfile, args.outputfile, args.interval, args.samples, args.time, args.column, args.mode)

    # Reading and plotting the results
    with open(args.outputfile, 'r') as file:
        lines = file.readlines()

    data = []
    for line in lines:
        values = [float(value) for value in line.split(",") if value]
        data.append(values)

    data = np.array(data)
    timestamp = data[:, 0]
    # print(timestamp)
    test_v = data[:, 1]

    l = len(timestamp) // 25
    time = {}
    pt = {}

    for i in range(25):
        time[i] = timestamp[i * l:(i + 1) * l]
        pt[i] = test_v[i * l:(i + 1) * l]

    for key in time:
        plt.plot(time[key], pt[key], label=f"Segment {key}")
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.grid()
    plt.show()
