import numpy as np

def select_func_gen(mode):
    def bmin(t1, v1, t2, v2, t): return v1
    def bmax(t1, v1, t2, v2, t): return v2
    def vmin(t1, v1, t2, v2, t): return min(v1, v2)
    def vmax(t1, v1, t2, v2, t): return max(v1, v2)
    def near(t1, v1, t2, v2, t): return v1 if t-t1 > t2-t else v2
    def mlin(t1, v1, t2, v2, t): return (t-t1)/(t2-t1) * (v2-v1) + v1

    if   (mode == "BMIN"): return bmin
    elif (mode == "BMAX"): return bmax
    elif (mode == "VMIN"): return vmin
    elif (mode == "VMAX"): return vmax
    elif (mode == "NEAREST"): return near
    elif (mode == "LINEAR" ): return mlin
    else: ValueError("Illegal mode selected")

def do_parse(file_in, file_out, sample_rate = 1e-6, samples = 1000, index = 0, sample_mode = "LINEAR"):

    col_t = index << 1
    col_v = col_t + 1

    time = np.linspace(0, sample_rate * samples, num=samples, endpoint=False)
    vals = np.zeros((samples,))
    interp = select_func_gen(sample_mode)

    with open (file_in, "r") as file:
        l = file.readline().strip().split()
        i  = 0

        tp = float(l[col_t])
        vp = float(l[col_v])

        time[i] = tp
        vals[i] = vp

        for line in file.readlines():
            l = line.strip().split()
            i += 1

            if i == samples: break
            t = time[i]
            
            tc = float(l[col_t])
            vc = float(l[col_v])

            if t >= tp: # and t < tc:
                vals[i] = interp(tp, vp, tc, vc, t)

            if t + sample_rate >= tc:
                tp = tc
                vp = vc

    with open (file_out, "w") as file:
        for t,v in zip(time, vals):
            file.write(f"{t},{v}\n")

if __name__ == "__main__": 
    import argparse

    argparser = argparse.ArgumentParser(prog="subsampler.py", description = "Subsample raw ngspice output to csv")
    argparser.add_argument("inputfile", type=str, help="Raw ngspice output data file to read")
    argparser.add_argument("outputfile", type=str, help="Target output csv file to write")
    argparser.add_argument("-t", "--step", type=float, default=1e-6, help="Subsampling step size")
    argparser.add_argument("-s", "--samples", type=int, default=100, help="Number of samples")
    argparser.add_argument("-i", "--index", type=int, default=0, help="Index of data to read from inputfile. Ignores time columns: 0 = first data column, 1 = second data column, etc.")
    argparser.add_argument("-m", "--mode", type=str, default="LINEAR", help="Subsampling mode: BMIN/BMAX use value at min/max bounding sample, VMIN/VMAX use min/max value of bounding samples, NEAREST use value from nearest sample, LINEAR linearly interpolate between samples")

    args = argparser.parse_args()
    do_parse(args.inputfile, args.outputfile, args.step, args.samples, args.index, args.mode)

