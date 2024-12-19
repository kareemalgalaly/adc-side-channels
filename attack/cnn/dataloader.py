from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import re

def get_files(directory, format, digital_index=0):

    format = re.compile(format)
    files = os.listdir(directory)

    #file_dict = {}
    file_list = [] # fname, fpath, label

    for fname in files:
        if match := format.match(fname):
            fpath = os.path.join(directory, fname)

            dvalue = int(match.groups()[digital_index])
            
            file_list.append((fname, fpath, dvalue))

            #if dvalue in file_dict:
            #    file_dict[dvalue].append(fpath)
            #else:
            #    file_dict[dvalue] = [fpath]

    return file_path #file_dict, file_path

class TraceDataset(Dataset):
    cached_traces = {}
    trace_list    = []

    def __init__(self, file_list, cache=True):
        self.file_list = file_list
        self.cache     = cache

    def __len__(self):
        return len(self.file_list)

    def __getitem__(self, index):
        fname, fpath, label = self.file_list[index]
        label = self.process_label(label)

        if self.cache and fname in self.cached_traces:
            return self.cached_traces[fname], label
        else:
            return self.load_trace(fname, fpath), label

    def get_info(self, index):
        return self.file_list[index]

    def load_trace(self, fname, fpath):
        with open(fpath, 'r') as file:
            header = file.readline()
            #time_arr = []
            valu_arr = []

            for line in file.readlines():
                time, value = line.strip().split()
                #time_arr.append(np.float32(time))
                valu_arr.append(np.float32(value))

        trace = np.array(valu_arr, dtype=np.float32)

        if self.cache: 
            self.cached_traces[fname] = trace
            self.trace_list.append(trace)

        return trace
    
    def process_label(self, label): return label

    def cache_all(self):
        assert self.cache == True

        print("Caching all traces")
        for fname, fpath, label in self.file_list:
            self.load_trace(fname, fpath)
        print("DONE Caching all traces")

class TraceDatasetBW(TraceDataset):
    def __init__(self, file_list, bit_select, cache=True):
        self.bit_mask = 1 << bit_select
        super().__init__(file_list, cache=cache)

    def process_label(self, label):
        return 1 if label & self.bit_mask else 0

class TraceDatasetBuilder:
    def __init__(self, adc_bitwidth=8, cache=True):
        self.file_list        = []
        self.cache = cache
        self.adc_bits = adc_bitwidth

        self.dataset = None
        self.dataloader = None
        self.datasets = []
        self.dataloaders = []

    def add_files(self, directory, format, label_group):
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

        for fname in fnames:
            if match := format.match(fname):
                fpath = os.path.join(directory, fname)
                dvalue = int(match.groups()[label_group])

                self.file_list.append((fname, fpath, dvalue))

    def build(self):
        self.dataset = TraceDataset(self.file_list, cache=self.cache)
        for b in range(self.adc_bits):
            self.datasets.append(TraceDatasetBW(self.file_list, b, cache=self.cache))

        if self.cache:
            self.dataset.cache_all()

    def build_dataloaders(self, **kwargs): # batch_size=256, shuffle=True
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

