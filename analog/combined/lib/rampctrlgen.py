import d_process
import sys
import random

## Config Params -------------------------------------------

NUM_CONTROL = 5         # Must be <= 8
NUM_SWITCH  = 4
PERIOD      = 256
RESET       = 2

## Computed Params -----------------------------------------

assert NUM_CONTROL <= 8
CONTROL_MASK = (1 << NUM_CONTROL) - 1
SWITCH_PERIOD = PERIOD / NUM_SWITCH


class RampControl:
    def __init__(self):
        self.reset()

    def reset(self):
        self.values = 0
        self.time_counter = 0
        self.next_switch  = RESET

    def compute(self, data_in, data_out, time):
        if time < 0: self.reset()

        if self.time_counter >= self.next_switch:
            self.next_switch = int(self.next_switch + SWITCH_PERIOD)
            self.values = random.randint(0, CONTROL_MASK) # TODO use cmpr or something else

        data_out[0] = self.values
        self.time_counter += 1
        return 1

process = d_process.DProcess(din=0, dout=NUM_CONTROL)
circuit = RampControl()
process.set_compute(circuit.compute, obj_mode=True)

process.main()

