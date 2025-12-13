###############################################################################
# File        : attack/cnn/utils.py
# Author      : kareem
# Created     : 2025 Dec 12
# Description : 
###############################################################################

import sys
from hashlib import shake_128

class ProgressBar:
    def __init__(self, f_start="", f_end="", bar_len=20, bar_chr='X', max_val=1, out=sys.stdout):
        self.out     = out
        self.f_start = f_start
        self.f_end   = f_end
        self.bar_len = bar_len
        self.bar_chr = bar_chr
        self.max_val = max_val

        self.val_len = len(str(max_val))
        #self.start_args = None
        #self.stop_args = None
        self.kwargs = {}

        self.running = False

    def start(self, **kwargs):
        self.kwargs = kwargs
        self.running = True
        self.update(0)

    def update(self, value, **kwargs):
        if not(self.running): return

        done = int(self.bar_len * value / self.max_val)
        remn = self.bar_len - done

        if kwargs is not {}: self.kwargs.update(kwargs)

        print(f"{self.f_start.format(**self.kwargs)}[{self.bar_chr*done}{('-'*(remn))}] {value:{self.val_len}}/{self.max_val} {self.f_end.format(**self.kwargs)}", end='\r', file=self.out, flush=True)

    def stop(self, value=-1):
        if not(self.running): return
        if value == -1: value = self.max_val

        print(f"{self.f_start.format(**self.kwargs)}[{self.bar_chr*self.bar_len}] {value:{self.val_len}}/{self.max_val} {self.f_end.format(**self.kwargs)}", file=self.out, flush=True)

        self.kwargs = {}
        self.running = False

# Base36 Hash ####################################

base36char = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base36(number):
    result = ""
    number = abs(number)
    while number != 0:
        number, remainder = divmod(number, 36)
        result += base36char[remainder]
    return result or base36char[0]

def base36hash(string):
    o = shake_128(string.encode('ascii'))
    b = o.digest(9)
    h = ""

    for i in range(0, len(b), 9):
        v = 0
        m = 1

        for j in range(0, 9):
            if i+j < len(b):
                #print("byte", j+i, b[i+j], m)
                v += b[j] * m
            else:
                break
            m = m << 8

        h += base36(v).rjust(14,"0")
        #print(h)
        #print(o.hexdigest(16))
    return h

    # 36 ^ 7 > 16 ^ 9
    # 36 ^ 14 > 16 ^ 18

