import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------
# func: knobs2slopelut
# - maps from the 5bit knobs to a ramp slope
#   where a slope of 1 means 1 peak-to-peak / sample period
# - equivalently this means that given a static knob for 
#   the entire sample period, 
#   slope = final peak-to-peak / nominal peak-to-peak
# - this version assumes the knobs linearly
#   interpolate between smin and smax
# ------------------------------------------------

def knobs2slopelut(knob, bits=5, smin=0.5, smax=1.5):
    kmax = 1 << bits
    knob &= kmax - 1
    return (knob / kmax) * (smax - smin) + smin

# ------------------------------------------------
# func: decode_counter
# - decodes the counter value 
# ------------------------------------------------

def decode_counter(count, knobs, sample_period=256, bits=5, smin=0.5, smax=1.5):
    steps = len(knobs)
    step_frac = 1 / steps
    full, rem = divmod(count, int(step_frac*sample_period))

    ncount = 0
    for i in range(full):
        slope = knobs2slopelut(knobs[i], bits, smin, smax)
        ncount += step_frac * slope * sample_period
    slope = knobs2slopelut(knobs[full], bits, smin, smax)
    ncount += rem * slope

    return int(ncount)

# Testing --------------------------------------------------

def test_decode(count, knobs, sample_period=256, bits=5, smin=0.5, smax=1.5):
    v = decode_counter(count, knobs, sample_period, bits, smin, smax)
    print(f"count = {count}, knobs = {knobs} -> {v}")

def plot_decode(count, knobs, sample_period=256, bits=5, smin=0.5, smax=1.5):
    v = decode_counter(count, knobs, sample_period, bits, smin, smax)
    print(f"count = {count}, knobs = {knobs} -> {v}")
    y = np.zeros(256)
    step_size = sample_period // len(knobs)

    a = 0
    i = 0

    for k in range(len(knobs)):
        slope = knobs2slopelut(knobs[k], bits, smin, smax)
        # step  = slope / sample_period
        step = slope
        for j in range(step_size):
            a += step
            y[i] = a
            i += 1

    plt.plot([v]*sample_period)
    plt.plot(y)
    plt.plot([count, count], [0, sample_period])
    plt.show()


# Main -----------------------------------------------------

if __name__ == "__main__":
    test_decode(100, [0]*4)
    test_decode(100, [1 << 4]*4)
    test_decode(100, [(1 << 5) - 1]*4)
    plot_decode(100, [1 << 4]*4)
    plot_decode(77, [0, 1 << 4, (1 << 5) - 1, 20])
    plot_decode(220, [5, 19, 11, 30])

