import sys
import struct

required_version = 0x01

## Utility Functions ---------------------------------------

# ------------------------------------------------
# func: printf
# ------------------------------------------------

def printf(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# ------------------------------------------------
# func: process_dlen(bits)
# - reutrns the number of bytes required to hold 
#   <bits> of data
# ------------------------------------------------

def process_dlen(bits):
    if bits == 0: return 0
    return int((bits - 1) // 8 + 1)

# ------------------------------------------------
# func: init
# - responds to ngspice header and initializes
#   the process handshake
# ------------------------------------------------

def init(pipein, pipeout, din_bits, dout_bits):
    header = pipein.read(3)

    if len(header) != 3:
        printf(f"Error: Incompatible ngspice d_process header size, requiring version {required_version}")
        pipeout.write(bytes(3))
        return 0

    version, din, dout = header
    if version != required_version or din != din_bits or dout != dout_bits:
        printf(f"Error: Incompatible ngspice d_process requiring version {required_version} got {version}, number of inputs {din} expected {din_bits}, and outputs {dout} expected {dout_bits}.")
        pipeout.write(bytes((required_version, din_bits, dout_bits)))
        return 0

    pipeout.write(header)
    pipeout.flush()
    printf(header.hex())
    return 1

def init_d(data_in, data_out):
    return init(data_in.pipein, data_out.pipeout, data_in.bits, data_out.bits)

## Data Structures -----------------------------------------

# ------------------------------------------------
# class: Data
# ------------------------------------------------

class Data:
    def __init__(self, bits):
        self.bits = bits
        self.nbytes = process_dlen(bits)
        self.data = bytes(self.nbytes)
        self.map = {}

    # --------------------------------------------
    # func: from_map
    # - mapping -> {name : (stop, start)}
    # --------------------------------------------

    @classmethod
    def from_map(cls, mapping, *args, **kwargs):
        max_bit = -1
        for rng in mapping.values():
            max_bit = max(*rng, max_bit)

        inst = cls(max_bit+1, *args, **kwargs)
        for key, value in mapping.items():
            inst.define(key, *value)

        return inst

    # --------------------------------------------
    # func: from_list
    # - mapping -> [(name, length)] 
    #   LSB first
    # --------------------------------------------

    @classmethod
    def from_list(cls, mapping, *args, **kwargs):
        bits = 0
        for name, length in mapping:
            bits += length

        inst = cls(bits, *args, **kwargs)
        bit = 0
        for name, length in mapping:
            inst.define(name, bit+length-1, bit)
            bit += length

        return inst

    def __len__(self):
        return self.nbytes

    def __getitem__(self, index):
        if isinstance(index, str):
            return self.get_bits(*self.map[index])
        return self.data[index]

    def __setitem__(self, index, value):
        if isinstance(index, str):
            return self.set_bits(*self.map[index], value)
        if index >= self.nbytes: raise IndexError("index out of range")
        self.data = self.data[:index] + bytes([value]) + self.data[index+1:]

    def get_all(self):
        return self.data

    def set_all(self, values):
        if len(data) != self.nbytes:
            raise ValueError(f"Data does not have correct size. Got {len(data)} Expected {self.dout}")
        else:
            self.data = data

    def get_bits(self, stop, start=-1):
        if start == -1: start = stop
        start_byte = start // 8
        start_bit  = start % 8
        stop_byte  = stop // 8
        stop_bit   = stop % 8
        aln = stop - start

        val = self[start_byte] >> start_bit
        vln = 8 - start_bit

        for i in range(start_byte+1, stop_byte+1):
            val |= (self[i] << vln)
            vln += 8

        msk = (1 << (aln+1)) - 1

        #print("val", hex(val))
        #print("msk", hex(msk))

        return val & msk

    def set_bits(self, stop, start, value):
        start_byte = start // 8
        start_bit  = start % 8
        stop_byte  = stop // 8
        stop_bit   = stop % 8
        aln = stop - start

        msk = (1 << (aln+1)) - 1
        #print("nmsk", bin(msk))
        val = msk & value
        msk = ~((1 << (stop - start_byte*8)) - 1) | ((1 << start_bit) - 1)
        #print("omsk", bin(msk))

        self[start_byte] = ((val << start_bit) & 0xff) | (self[start_byte] & msk)
        val = val >> (8 - start_bit)
        msk = msk >> 8

        for i in range(start_byte+1, stop_byte+1):
            self[i] = val 
            val = val >> 8
            msk = msk >> 8

    def define(self, name, stop, start=-1):
        if start == -1: start = stop
        #printf(f"setting {name} -> {stop}:{start}")
        self.map[name] = (stop, start)

    def read(self, stream):
        #printf("read", self.nbytes, stream)
        self.data = stream.read(self.nbytes)
        return len(self.data) == len(self)

    def write(self, stream):
        r = stream.write(self.data) == len(self)
        stream.flush()
        return r
         

# ------------------------------------------------
# class: DataIn
# - structure for reading data from ngspice
# ------------------------------------------------

class DataIn(Data):
    def __init__(self, bits, pipein=sys.stdin.buffer):
        self.pipein = pipein
        self.time = 0
        super().__init__(bits)

    def read(self):
        data = self.pipein.read(self.nbytes+8)
        if len(data) != self.nbytes + 8: 
            #printf(len(self.data), self.data, self.nbytes + 8)
            return 0

        self.time = struct.unpack("d", data[:8])[0]
        self.data = data[8:]
        return 1
    #return super().read(self.pipein)

# ------------------------------------------------
# class: DataOut
# - structure for writing data to ngspice
# ------------------------------------------------

class DataOut(Data):
    def __init__(self, bits, pipeout=sys.stdout.buffer):
        self.pipeout = pipeout
        super().__init__(bits)

    def write(self):
        return super().write(self.pipeout)

## DProcess ------------------------------------------------
# Helper class for managing inter-process communcation
# with ngspice

class DProcess:
    def __init__(self, din=0, dout=0, pipein=sys.stdin.buffer, pipeout=sys.stdout.buffer, data_in=None, data_out=None):
        self.data_in  = data_in  if data_in  else DataIn(din, pipein)
        self.data_out = data_out if data_out else DataOut(dout, pipeout)
        self.din      = self.data_in.bits
        self.dout     = self.data_out.bits
        self.computef = None

    def set_compute(self, f, obj_mode=False):
        self.computef = f
        self.obj_mode = obj_mode

    def get_data_in(self):
        return self.data_in

    def get_data_out(self):
        return self.data_out

    def compute(self, data_in, data_out, time):
        if self.obj_mode:
            return self.computef(data_in, data_out, time)

        try:
            data_out.set_all(self.compute(data_in.get_all(), time))
            return 1
        except Exception as e:
            printf("compute() raised exception:", e)
            return 0
        #v = bytes([0xd0])
        #if self.din: v = data_in.get_all()

        #for i in range(min(len(data_in), len(data_out))):
        #    data_out[i] = data_in[i]

        #for i in range(len(data_in), len(data_out)):
        #    data_out[i] = time

        #return 1

    def main(self):
        if not init_d(self.data_in, self.data_out): return -1

        try:
            i = 0
            while (self.data_in.read()):
                if not self.compute(self.data_in, self.data_out, self.data_in.time):
                    printf("Error: Compute Failed")
                    return 1
                i += 1
                self.data_out.write()
        except (BrokenPipeError, IOError, KeyboardInterrupt) as e:
            pass

        printf(f"DProcess <{sys.argv[0]}> Exiting after {i} loops...")
        #bs = sys.stdin.buffer.read()
        #printf(f"Dumping remaining stdin [{len(bs)}]\n{bs.hex()}")
        sys.stderr.close()
        return 0


