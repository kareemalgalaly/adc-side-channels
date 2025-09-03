###############################################################################
# File        : attack/cnn/pt_parser.py
# Author      : 
# Created     : 
# Description : Original parsing setup, no longer used
###############################################################################

import os
import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from collections import defaultdict

# Base class for dataset of each power trace
# Each dataset represents a single dnode, or digital value
class PowerTraceDataSet(Dataset):
    def __init__(self, input, label):
        self.inputs = input
        self.labels = label
    
    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        x = self.inputs[idx]
        y = self.labels[idx]
        return x, y

# Creates datasets for all digital values
# Input:
# 1) directory: root path of CNN_PSA folder
# Assumes there is a folder named "powertraces" storing power trace output with syntax "out_{i}.txt"
# 2) adc_bit: total number of bits of ADC, creates adc_bit number of datasets
# Output:
# 1) self.files: list of output files with name syntax "out_{i}.txt"
# 2) self.powertraces: TENSOR that contains all powertraces obtained from output files
# 3) self.labels: DICTIONARY of TENSORS that contains all labels obtained from output files
# 4) self.datasets: DICTIONARY of DATASETS per each digital node, index is each dnode index(d0 = 0, etc.)
class createPowerTraceDataSet():
    def __init__(self, directory, adc_bit):
        if adc_bit <= 0:
            raise KeyError(f"Number of bits in ADC should be larger than 0(current value: {adc_bit})")
        directory = directory + "/powertraces"
        self.files = [f for i in range(256) for f in os.listdir(directory) if f == f"out_{i}.txt"]
        if len(self.files) == 0:
            raise FileNotFoundError(f"No files found: format 'out_i.txt' in directory: {directory}")
        
        min_length = float('inf')
        for file_name in self.files:
            file_path = os.path.join(directory, file_name)
            data = pd.read_csv(file_path, sep='\s+')
            trace_length = len(data['-i(vdd)'].values[1:])
            if trace_length < min_length:
                min_length = trace_length

        self.powertraces = np.empty((len(self.files), min_length), dtype=np.float32)
        self.labels=defaultdict(list)
        # Load and process each file
        for idx, file_name in enumerate(self.files):
            file_path = os.path.join(directory, file_name)
            data = pd.read_csv(file_path, sep='\s+')
            trace = data['-i(vdd)'].values[1:min_length+1]
            self.powertraces[idx, :] = trace
            for i in range(adc_bit):
                if data.iloc[-2, i + 3] != 0:
                    self.labels[i].append(1)
                else:
                    self.labels[i].append(0)
        
        print("File parsing complete, creating datasets...")
        
        self.powertraces = torch.tensor(self.powertraces, dtype=torch.float32)
        for key in self.labels.keys():
            self.labels[key] = np.array(self.labels[key], dtype=np.float32)
            self.labels[key] = torch.tensor(self.labels[key], dtype=torch.float32)
        self.datasets = {}
        for i in range(adc_bit):
            self.datasets[i]=PowerTraceDataSet(self.powertraces, self.labels[i])

'''
# LOCAL TEST CODE
directory = os.path.dirname(os.path.abspath(__file__))
# dictionary to store datasets for each label (d0 to d7)
total = createPowerTraceDataSet(directory, 8).datasets
dataloaders = {}

for i in range(8):
    dataloaders[i] = DataLoader(total[i], batch_size=256, shuffle=True)
    print(f"Created dataloader for d{i}")

    for inputs, labels in dataloaders[i]:
        print(f'Inputs: {inputs}')
        print(f'Labels (d{i}): {labels}')
        break
'''
