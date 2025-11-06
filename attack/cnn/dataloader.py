###############################################################################
# File        : attack/cnn/dataloader.py
# Author      : kareemahmad
# Created     : 
# Description : Defines dataset related classes
#   TraceDataset 
#     - holds labelled processed traces
#     - is directly consumed by DataLoader()
#     - defines trace loading (from file), processing, and caching
#   TraceDatasetBW
#     - same as TraceDataset but processes labels to extract bit information 
#       from full digital value
#   TraceDatasetBuilder
#     - class that wraps multiple TraceDatasets to build all the sub-datasets
#       required for a single ADC (eg 1 TraceDataset + 8 TraceDatasetBW for 
#       simulation of 1 ADC design at a given corner)
#     - holds dataloaders for the TraceDataset objects
###############################################################################

from torch.utils.data import Dataset, DataLoader
from collections import namedtuple
from subsampler import sample_file
from normalizer import build_normalizer
# TODO other sample_file
import numpy as np
import os
import re

## Types ---------------------------------------------------

TraceInfo = namedtuple("TraceInfo", ["trace", "start", "stop"])
FileInfo  = namedtuple("FileInfo", ["fname", "fpath", "label", "sample_info"])
DTYPE = np.float32

## Trace Cache ---------------------------------------------

class TraceCache:
    def __init__(self, file_list, label_dict, cols=1, nparams={}):
        self.file_list  = file_list
        self.label_dict = label_dict
        self.raw_cache  = [None] * len(file_list) # list of trace info (w/ raw trace)
        self.nrm_cache  = [None] * len(file_list) # list of normalized traces
        self.cols       = cols
        self.normalizer = build_normalizer(self, nparams)

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, index):
        if (trace:=self.nrm_cache[index]) is None:
            if self.raw_cache[index] is None: self.get_raw(index)
            trace = self.normalizer.fit(index)
        return trace

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def get_by_label(self, label, index=-1, raw=False):
        gf      = self.get_raw if raw else self.__getitem__ 
        indices = self.label_dict[label]

        if index == -1:
            return [gf(i) for i in indices]
        return gf(index)

    def get_raw(self, index):
        if (tinf:=self.raw_cache[index]) is None:
            fname, fpath, label, sample_info = self.file_list[index]
            tinf = self.load_trace(fpath, sample_info)
            self.raw_cache[index] = tinf
        return tinf

    def iter_raw(self):
        for i in range(len(self)):
            yield self.get_raw(i)

    def load_trace(self, fpath, sample_info):
        sample_mode, sample_int, max_sample = sample_info

        # timed
        if sample_mode == 'timed':
            with open(fpath, 'r') as file:
                header = file.readline()
                if self.cols == 1:
                    splitf = lambda x: (DTYPE(x[0]), DTYPE(x[1]))
                else:
                    splitf = lambda x: (DTYPE(x[0]), *[DTYPE(xi) for xi in x[1:]])

                valu_arr = [splitf(line.strip().split()) for line in file.readlines()]
                time_arr, *valu_arr = zip(*valu_arr)

                if self.cols == 1:
                    trace = np.array(valu_arr[0], dtype=DTYPE)
                else:
                    trace = np.stack([np.array(va, dtype=DTYPE) for va in valu_arr], axis=0)
                trace = (time_arr, trace)

                tstart = time_arr[0]
                tstop  = time_arr[-1]

        # sampled
        elif sample_mode:
            valu_arr, tstart, tstop = sample_file(fpath, sample_int, max_sample, sample_mode=sample_mode, cols=self.cols)
            if self.cols == 1:
                trace = np.array(valu_arr[0], dtype=DTYPE)
            else:
                trace = np.stack([np.array(va, dtype=DTYPE) for va in valu_arr], axis=0)

        # raw
        else:
            with open(fpath, 'r') as file:
                header = file.readline()
                tstart, *val = file.readline().strip().split()
                valu_arr = [[DTYPE(v)] for v in val]
                for line in file.readlines():
                    tcurr, *val = line.strip().split()
                    for i, v in enumerate(val):
                        valu_arr[i].append(DTYPE(val))
                tstop = DTYPE(tcurr)

                if self.cols == 1:
                    trace = np.array(valu_arr[0], dtype=DTYPE)[:max_sample]
                else:
                    trace = np.stack([np.array(va, dtype=DTYPE) for va in valu_arr], axis=0)[:, :max_sample]

        return TraceInfo(trace, tstart, tstop)


class TraceDataset(Dataset):
    def __init__(self, file_list, label_dict, cache, cols=1, device=None):
        self.file_list  = file_list
        self.label_dict = label_dict
        self.cache      = cache
        self.device     = device
        self.cols       = cols

        self.set_prop_range(0, 1)

    def __len__(self):
        #return len(self.file_list)
        return self.stop - self.start

    def __getitem__(self, index):
        index += self.start
        trace = self.cache[index]
        label = self.process_label(self.file_list[index].label)
        return trace, label

    def get_info(self, index):
        tinf  = self.cache.get_raw(index)
        trace = self.cache[index]
        label = self.process_label(self.file_list[index].label)
        return TraceInfo(trace, tinf.start, tinf.stop), label

    def get_by_label(self, label, index=0):
        if index == -1:
            return [self.get_by_label(label, i) for i in range(len(self.label_dict[label]))]

        index = self.label_dict[label][index]
        return self.get_info(index)[0]

    def set_range(self, start, stop):
        self.start = start
        self.stop  = stop
        return self

    def set_prop_range(self, test, proportion):
        width = int(len(self.file_list) * proportion)
        start = len(self.file_list) - width if test else 0
        stop  = start + width
        self.set_range(start, stop)
        return self
 
    def process_label(self, label): 
        return DTYPE(label)

class TraceDatasetBW(TraceDataset):
    def __init__(self, file_list, label_dict, cache, bit_select, cols=1, device=None):
        self.bit_mask = 1 << bit_select
        super().__init__(file_list, label_dict, cache, cols=cols, device=device)

    def process_label(self, label):
        return 1 if label & self.bit_mask else 0

class TraceDatasetBuilder:
    def __init__(self, adc_bitwidth=8, cols=1, nparams={}, device=None):
        self.file_list  = []
        self.label_dict = {}
        self.cols       = cols
        self.cache      = None
        self.nparams    = nparams
        self.adc_bits   = adc_bitwidth
        self.device     = device

        self.dataset    = None
        self.dataloader = None
        self.datasets   = []
        self.dataloaders = []

        self.trace_cache = {}

    def add_files(self, directory, format, label_func=lambda gs: int(gs[0]), sample_mode=None, sample_int=0.1e-6, sample_time=300e-6, max_sample=None):
        ''' Builds list of powertrace files
        Inputs:
            directory   : folder to search for files
            format      : regular expression to match filenames
            label_index : group index for digital output label corresponding to trace
        Outputs:
            list        : [(file_name, file_path, label) ... ]
        '''
        format = re.compile(format)
        fnames = os.listdir(directory)

        if sample_mode: max_sample = int(sample_time / sample_int)
        sample_info = (sample_mode, sample_int, max_sample)

        i = 0
        for fname in fnames:
            if match := format.match(fname):
                fpath = os.path.join(directory, fname)
                dvalue = label_func(match.groups())

                self.file_list.append(FileInfo(fname, fpath, dvalue, sample_info))

                if dvalue in self.label_dict: self.label_dict[dvalue].append(i)
                else:                         self.label_dict[dvalue] = [i]
                i += 1

    def build(self):
        self.cache   = TraceCache(self.file_list, self.label_dict, self.cols, self.nparams)
        self.dataset = TraceDataset(self.file_list, self.label_dict, self.cache, cols=self.cols, device=self.device)
        for b in range(self.adc_bits):
            self.datasets.append(TraceDatasetBW(self.file_list, self.label_dict, self.cache, b, cols=self.cols, device=self.device))

    def build_dataloaders(self, test=0, proportion=1, **kwargs): # batch_size=256, shuffle=True
        if self.device and 'pin_memory' not in kwargs: kwargs['pin_memory'] = True

        self.dataloader = DataLoader(self.dataset.set_prop_range(test, proportion), **kwargs)
        self.dataloaders = [DataLoader(dataset.set_prop_range(test, proportion), **kwargs) for dataset in self.datasets]

if __name__ == '__main__':
    #pwd = os.path.dirname(os.path.abspath(__file__))
    pwd = "/Users/kareemahmad/Projects/SideChannels/SingleSlopeADC_Mixed/analog/outfiles/sky"

    bld = TraceDatasetBuilder(8, cache=False)
    bld.add_files(pwd, format="sky_d(\\d+)_.*\\.txt")
    bld.build()

    print(bld.dataset[0])

