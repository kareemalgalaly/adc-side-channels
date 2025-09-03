import d_process
import sys

printf = d_process.printf

class RArray:
    def __init__(self, pxls=1, bits=8):
        self.pixels = pxls
        self.max_value = (1 << bits) - 1

    def compute(self, data_in, data_out, time):
        if time < 0:
            for i in range(self.pixels):
                data_out[f"pixel{i}"] = 0
                return 1

        en = data_in["enable"] 
        ct = data_in["count"]

        for i in range(self.pixels):
            if en & (1 << i):
                data_out[f"pixel{i}"] = ct

        return 1
                    
pxls = int(sys.argv[1]) if len(sys.argv) >= 2 else 1
bits = int(sys.argv[2]) if len(sys.argv) >= 3 else 8

rarray = RArray(bits=bits)
data_in = d_process.DataIn.from_list((
    ("enable" , pxls),
    ("count"  , bits),
    ))
data_out = d_process.DataOut.from_list([
    (f"pixel{i}", bits) for i in range(pxls)
    ])

process = d_process.DProcess(data_in=data_in, data_out=data_out)
process.set_compute(rarray.compute, obj_mode=True)

process.main() # 0 = ok, -1 = failed init, 1 = failed compute
