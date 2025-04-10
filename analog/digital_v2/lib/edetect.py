import d_process

#d = d_process.Data(4)
#
#d[0] = 0xef
#d[1] = 0xbe
#d[2] = 0xad
#d[3] = 0xde
#
#print(hex(d.get_bits(15,0)))
#print(hex(d.get_bits(31,16)))
#
#print(bin(d.get_bits(31,0)))
#print(bin(d.get_bits(4,2)))
#
#d.set_bits(4,2,0xf)
#print(bin(d.get_bits(31,0)))

class Edetect:
    def __init__(self):
        self.seen = 0

    def compute(self, data_in, data_out, time):
        if time < 0:
            self.seen = 0
            self.data_out[0] = 0

        elif data_in[0]:
            if self.seen: 
                data_out[0] = 0
            else:
                self.seen = 1
                data_out[0] = 1

        else:
            data_out[0] = 0

        return 1

process = d_process.DProcess(din=0, dout=8)
counter = Counter()
process.set_compute(counter.compute, obj_mode=True)

process.main() # 0 = ok, -1 = failed init, 1 = failed compute

