import d_process
import sys

class Counter:
    def __init__(self, bits=8):
        self.value = 0
        self.max_value = (1 << bits) - 1

    def compute(self, data_in, data_out, time, tick):
        if time < 0:
            self.value = 0

        elif tick:
            if data_in['enable']:
                if data_in['write']:
                    self.value = data_in['wdata']
                elif self.value == self.max_value:
                    self.value = 0
                else:
                    self.value += 1

        # d_process.printf(f"\nTime: {round(time*1e6,1):5}    Value: {self.value:3}      {time}")

        data_out[0] = self.value
        return 1

# bits = int(sys.argv[1]) if len(sys.argv) == 2 else 8

data_in = d_process.DataIn.from_map(dict(
        enable = (0, 0),
        write  = (1, 1),
        wdata  = (9, 2),
    ))
data_out = d_process.DataOut.from_map(dict(
        counter = (7, 0),
        overflow = (8, 8)
    ))

process = d_process.DProcess(data_in=data_in, data_out=data_out)
counter = Counter(bits=bits)
process.set_compute(counter.compute, obj_mode=True, report_tick=True)

process.main() # 0 = ok, -1 = failed init, 1 = failed compute
