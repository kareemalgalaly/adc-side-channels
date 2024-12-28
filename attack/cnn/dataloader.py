import torch
from torch.utils.data import Dataset, DataLoader
from subsampler import sample_file
import numpy as np
import os
import re

def get_files(directory, format, digital_index=0):

    format = re.compile(format)
    files = os.listdir(directory)

    label_dict = {} # label : index (in file_list)
    file_list = [] # fname, fpath, label
    sample_info = (sample_mode, sample_int, max_sample)

    i = 0
    for fname in files:
        if match := format.match(fname):
            fpath = os.path.join(directory, fname)

            dvalue = int(match.groups()[digital_index])
            
            file_list.append((fname, fpath, dvalue, sample_info))

            if dvalue in label_dict:
                label_dict[dvalue].append(i)
            else:
                label_dict[dvalue] = [i]

            i += 1

    return file_path, label_dict

class TraceDataset(Dataset):
    cached_traces = {}
    labelled_traces = {}
    trace_list    = []

    def __init__(self, file_list, label_dict, cache=True, device=None):
        self.file_list  = file_list
        self.label_dict = label_dict
        self.cache      = cache
        self.device     = device

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, index):
        fname, fpath, label, sample_info = self.file_list[index]
        label = self.process_label(label)

        if self.cache and fname in self.cached_traces:
            return self.cached_traces[fname], label
        else:
            return self.load_trace(fname, fpath, label, sample_info), label

    def get_info(self, index):
        return self.file_list[index]

    def get_by_label(self, label, index=0):
        index = self.label_dict[label][index]
        return self[index][0]

    def load_trace(self, fname, fpath, label, sample_info):
        sample_mode, sample_int, max_sample = sample_info

        if sample_mode:
            valu_arr = sample_file(fpath, sample_int, max_sample, sample_mode=sample_mode)
        else:
            with open(fpath, 'r') as file:
                header = file.readline()
                valu_arr = [np.float32(line.strip().split()[1]) for line in file.readlines()]

        trace = np.array(valu_arr, dtype=np.float32)
        #trace = torch.tensor(valu_arr, dtype=torch.float32, device=self.device)

        if self.cache: 
            self.cached_traces[fname] = trace
            self.trace_list.append(trace)

            if label in self.labelled_traces:
                self.labelled_traces[label].append(trace)
            else:
                self.labelled_traces[label] = [trace]

        return trace
    
    def process_label(self, label): return label

    def cache_all(self):
        assert self.cache == True

        print("Caching all traces")
        for args in self.file_list:
            self.load_trace(*args)
        print("DONE Caching all traces")

class TraceDatasetBW(TraceDataset):
    def __init__(self, file_list, label_dict, bit_select, cache=True, device=None):
        self.bit_mask = 1 << bit_select
        super().__init__(file_list, label_dict, cache=cache, device=device)

    def process_label(self, label):
        return 1 if label & self.bit_mask else 0

class TraceDatasetBuilder:
    def __init__(self, adc_bitwidth=8, cache=True, device=None):
        self.file_list  = []
        self.label_dict = {}
        self.cache      = cache
        self.adc_bits   = adc_bitwidth
        self.device     = device

        self.dataset    = None
        self.dataloader = None
        self.datasets   = []
        self.dataloaders = []

    def add_files(self, directory, format, label_group=0, sample_mode=None, sample_int=0.1e-6, sample_time=300e-6):
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

        max_sample = sample_time / sample_int if sample_mode else None
        sample_info = (sample_mode, sample_int, max_sample)

        i = 0
        for fname in fnames:
            if match := format.match(fname):
                fpath = os.path.join(directory, fname)
                dvalue = int(match.groups()[label_group])

                self.file_list.append((fname, fpath, dvalue, sample_info))

                if dvalue in self.label_dict: self.label_dict[dvalue].append(i)
                else:                         self.label_dict[dvalue] = [i]
                i += 1

    def build(self):
        self.dataset = TraceDataset(self.file_list, self.label_dict, cache=self.cache, device=self.device)
        for b in range(self.adc_bits):
            self.datasets.append(TraceDatasetBW(self.file_list, self.label_dict, b, cache=self.cache, device=self.device))

    def cache_all(self):
        assert self.cache
        self.dataset.cache_all()

    def build_dataloaders(self, **kwargs): # batch_size=256, shuffle=True
        if self.device and 'pin_memory' not in kwargs: kwargs['pin_memory'] = True

        self.dataloader = DataLoader(self.dataset, **kwargs)
        self.dataloaders = [DataLoader(dataset, **kwargs) for dataset in self.datasets]

if __name__ == '__main__':
    #pwd = os.path.dirname(os.path.abspath(__file__))
    pwd = "/Users/kareemahmad/Projects/SideChannels/SingleSlopeADC_Mixed/analog/outfiles/sky"

    bld = TraceDatasetBuilder(8, cache=False)
    bld.add_files(pwd, format="sky_d(\\d+)_.*\\.txt", label_group=0)
    bld.build()

    print(bld.dataset.get_info(0))
    print(bld.dataset[0])

