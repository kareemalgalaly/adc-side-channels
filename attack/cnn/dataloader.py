from torch.utils.data import Dataset, DataLoader
from collections import namedtuple
from subsampler import sample_file
import numpy as np
import os
import re

TraceInfo = namedtuple("TraceInfo", ["trace", "start", "stop"])

DTYPE = np.float32

class TraceDataset(Dataset):
    labelled_traces = {}
    trace_list    = []

    def __init__(self, file_list, label_dict, mult=1e4, cache=True, trace_cache={}, device=None):
        self.file_list  = file_list
        self.label_dict = label_dict
        self.cache      = cache
        self.device     = device
        self.mult       = mult

        if cache: self.trace_cache = trace_cache
        self.set_prop_range(0, 1)

    def __len__(self):
        #return len(self.file_list)
        return self.stop - self.start

    def __getitem__(self, index):
        traceinfo, label = self.get_item(self.start + index)
        return traceinfo.trace, label

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

    def get_item(self, index):
        fname, fpath, label, sample_info = self.file_list[index]
        label = self.process_label(label)

        if self.cache and fpath in self.trace_cache:
            return self.trace_cache[fpath], label
        else:
            return self.load_trace(fname, fpath, label, sample_info), label

    def get_info(self, index):
        return self.file_list[index]

    def get_by_label(self, label, index=0):
        index = self.label_dict[label][index]
        return self.get_item(index)[0]

    def load_trace(self, fname, fpath, label, sample_info):
        sample_mode, sample_int, max_sample = sample_info

        if sample_mode == 'timed':
            with open(fpath, 'r') as file:
                header = file.readline()
                splitf = lambda x: (DTYPE(x[0]), DTYPE(x[1])*self.mult)

                valu_arr = [splitf(line.strip().split()) for line in file.readlines()]
                time_arr, valu_arr = zip(*valu_arr)
                trace = np.array((time_arr, valu_arr), dtype=DTYPE)
                tstart = time_arr[0]
                tstop  = time_arr[-1]

        elif sample_mode:
            valu_arr, tstart, tstop = sample_file(fpath, sample_int, max_sample, sample_mode=sample_mode)
            trace = np.array(valu_arr, dtype=DTYPE)*self.mult

        else:
            with open(fpath, 'r') as file:
                header = file.readline()
                tstart, val = file.readline().strip().split()
                valu_arr = [DTYPE(val)]
                for line in file.readlines():
                    tcurr, val = line.strip().split()
                    valu_arr.append(DTYPE(val))
                tstop = DTYPE(tcurr)
                trace = np.array(valu_arr, dtype=DTYPE)[:max_sample]*self.mult

        trace_info = TraceInfo(trace, tstart, tstop)

        if self.cache: 
            self.trace_cache[fpath] = trace_info
            self.trace_list.append(trace)

            if label in self.labelled_traces:
                self.labelled_traces[label].append(trace)
            else:
                self.labelled_traces[label] = [trace]

        return trace_info
    
    def process_label(self, label): return DTYPE(label)

    def cache_all(self):
        assert self.cache == True

        print("Caching all traces")
        for args in self.file_list:
            self.load_trace(*args)
        print("DONE Caching all traces")

class TraceDatasetBW(TraceDataset):
    def __init__(self, file_list, label_dict, bit_select, mult=1e4, cache=True, trace_cache={}, device=None):
        self.bit_mask = 1 << bit_select
        super().__init__(file_list, label_dict, mult=mult, cache=cache, trace_cache=trace_cache, device=device)

    def process_label(self, label):
        return 1 if label & self.bit_mask else 0

class TraceDatasetBuilder:
    def __init__(self, adc_bitwidth=8, mult=1e4, cache=True, device=None):
        self.file_list  = []
        self.label_dict = {}
        self.mult       = mult
        self.cache      = cache
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

                self.file_list.append((fname, fpath, dvalue, sample_info))

                if dvalue in self.label_dict: self.label_dict[dvalue].append(i)
                else:                         self.label_dict[dvalue] = [i]
                i += 1

    def build(self):
        self.dataset = TraceDataset(self.file_list, self.label_dict, mult=self.mult, cache=self.cache, trace_cache=self.trace_cache, device=self.device)
        for b in range(self.adc_bits):
            self.datasets.append(TraceDatasetBW(self.file_list, self.label_dict, b, mult=self.mult, cache=self.cache, trace_cache=self.trace_cache, device=self.device))

    def cache_all(self):
        assert self.cache
        self.dataset.cache_all()

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

    print(bld.d0ataset.get_info(0))
    print(bld.dataset[0])

