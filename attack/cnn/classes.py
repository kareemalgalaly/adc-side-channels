###############################################################################
# File        : /Users/kareemahmad/Projects/SideChannels/adc-side-channel/attack/cnn/classes.py
# Author      : kareemahmad
# Created     :
# Description : python class definitions for types in regression.json
#   classes extend HashableBase to provide a unique hash id for identifying 
#   known commands
###############################################################################


import os
import sys
import json
import argparse
import datetime

import torch.nn as nn
import torch.optim as optim

from copy import copy
from hashlib import shake_128

from dataloader import TraceDatasetBuilder, TraceInfo
from cnn_gen import GenericCNN

# Args Base ######################################

argparser = argparse.ArgumentParser()
argparser.add_argument("-i", "--json",   type=str, default='regression.json', help="JSON description of CNNs")
argparser.add_argument("-o", "--output", type=str, default='outputs', help="Directory for output files")

# Base Paths #####################################

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')

# Helpers ########################################

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

# Base ###########################################

class HashableBase:
    def __str__(self):
        csv = self.get_csv()
        return f"{base36hash(csv)},{csv}"

    def hash(self):
        return base36hash(self.get_csv())

    def get_csv(self):
        raise NotImplementedError("HashableBase should not be instantiated directly")

# Network ########################################

# ------------------------------------------------
# class: Network
# - Python class corresponding to the network
#   objects in regression.json
# - Can be predefined CNNs extracted from 
#   torchvision.models (in progress)
# - Can be defined using the GenericCNN string 
#   format from cnn_gen
# ------------------------------------------------

class Network(HashableBase):
    def __init__(self, name, info, args):
        self.name       = name
        self.definition = info['definition']
        self.type       = info['type']
        self.inputs     = info['inputs']
        self.weights    = info.get('weights', None)
        self.predef     = self.definition.startswith("predef::")
        self.preprocess = eval(f"lambda x: {info.get('preprocess', 'x')}")

        self.args = args

    # --------------------------------------------
    # func: get_csv
    # - Returns the csv description string for this network
    # --------------------------------------------

    def get_csv(self):
        return f"{self.type},{self.definition.replace(',',';')},{self.inputs}"

    # --------------------------------------------
    # func: create
    # - Returns the pytorch neural network object
    #   corresponding to the defined network
    # --------------------------------------------

    def create(self, input_len, input_ch):
        # predef is not fully functional
        if self.predef:
            import torchvision
            network_class   = getattr(torchvision.models, self.definition[8:])
            network = network_class(weights = self.weights)

            #if self.weights:
            #    #weights, flavor = self.weights.split(".")
            #    #network_weights = getattr(torchvision.models, weights)
            #    #network_weights = getattr(network_weights, flavor)
            #    #self.preprocess = network_weights.transforms()
            #    network = network_class(weights = self.weights)
            #else:
            #    network = network_class(pretrained=False)

            network.eval()

            return network
        else:
            desc = f"{input_len},{input_ch}:{self.definition}"
            try:
                return GenericCNN(desc, self.inputs, debug=self.args.nndebug)
            except Exception as e:
                print("Failed to create:", desc)
                print(e)
                return None

# Dataset ########################################

# ------------------------------------------------
# class: Dataset
# - Python class corresponding to dataset objects
#   in regression.json 
# ------------------------------------------------

class Dataset(HashableBase):
    
    # --------------------------------------------
    # func: __init__
    # - type: one of (raw, timed, sampled)
    #   + raw = use trace file as is (assumes       < Legacy option
    #       equally spaced entries)
    #   + timed = use trace file as is (does not    < Used for plotting only
    #       assume equally spaced entries, but
    #       also does not correct)
    #       only used to plot original traces
    #   + sampled = resample trace to produce       < Used for CNNs in papers
    #       evenly spaced samples 
    # - lblf: function to generate label from 
    #   file regex
    # - paths: paths to search for trace files
    # --------------------------------------------

    def __init__(self, name, info, defaults):
        self.name = name
        self.type = info['type']
        self.frmt = info['format']
        self.cols = info['columns']
        self.lblf = eval(info.get("label", "lambda gs: int(gs[0])"), globals(), {})
        self.paths = [path if path.startswith("/") else os.path.join(data_dir, path) for path in info.get('paths', [])]

        self.trace_scale = info.get("trace_scale", defaults["trace_scale"])

        if path := info.get('path', None):
            self.paths.append(os.path.join(data_dir, path))
        self.builder = None

    # --------------------------------------------
    # func: from_info
    # - creates corresponding dataset subtype from 
    #   json description
    # --------------------------------------------

    @classmethod
    def from_info(cls, name, info, defaults):
        if info['type'] == 'raw':
            return RawDataset(name, info, defaults)
        elif info['type'] == 'timed':
            return TimedDataset(name, info, defaults)
        else:
            return SampledDataset(name, info, defaults)

    # --------------------------------------------
    # func: get_csv
    # - Returns the csv description string for this network
    # --------------------------------------------

    def get_csv(self):
        return f"{self.type},{';'.join(os.path.basename(path) for path in self.paths)},{self.cols}"

    # --------------------------------------------
    # func: build
    # - Retuns dataset builder, creating it if it 
    #   doesn't already exist
    # --------------------------------------------

    def build(self, adc_bitwidth=8, device=None):
        if self.builder: return self.builder
        self.builder = TraceDatasetBuilder(adc_bitwidth=adc_bitwidth, mult=self.trace_scale, cache=True, device=device, cols=self.cols)
        return self.builder

    # --------------------------------------------
    # func: get_trace
    # - Returns the trace corresponding to the 
    #   specified label (as a TraceInfo object)
    # --------------------------------------------
    
    def get_trace(self, label, index=0, bit=-1):
        dataset = self.builder.dataset if bit == -1 else self.builder.datasets[bit]

        # Specific trace (index = -1 gets all of them)
        if label != -1:
            return dataset.get_by_label(label, index=index)
        
        # Average trace
        (sum, start, stop), label = dataset.get_item(0)
        for i in range(1, len(dataset)):
            sum += dataset[i][0]
        return TraceInfo(sum / len(dataset), start, stop)

# ------------------------------------------------
# class: RawDataset
# - Python class corresponding to dataset objects
#   of *raw* type
# ------------------------------------------------

class RawDataset(Dataset):
    def __init__(self, name, info, defaults):
        assert info['type'] == 'raw'
        super().__init__(name, info, defaults)

        self.len  = info['len']

    def get_csv(self):
        return f"{super().get_csv()},{self.len}"

    def build(self, adc_bitwidth=8, device=None):
        if self.builder: return self.builder
        super().build(adc_bitwidth, device)
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, max_sample=self.len)
        self.builder.build()
        return self.builder

# ------------------------------------------------
# class: SampledDataset
# - Python class corresponding to dataset objects
#   of *sampled* type
# ------------------------------------------------

class SampledDataset(Dataset):
    def __init__(self, name, info, defaults):
        assert info['type'] == 'sampled'
        super().__init__(name, info, defaults)

        self.mode     =  info['sample_mode']
        self.interval =  info['sample_interval']
        self.duration =  info['sample_duration']
        self.len      = int(self.duration / self.interval)

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        if self.builder: return self.builder
        super().build(adc_bitwidth, device)
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, sample_mode=self.mode, sample_int=self.interval, sample_time=self.duration)
        self.builder.build()
        return self.builder

# ------------------------------------------------
# class: TimedDataset
# - Python class corresponding to dataset objects
#   of *timed* type
# ------------------------------------------------

class TimedDataset(Dataset):
    def __init__(self, name, info, defaults):
        assert info['type'] == 'timed'
        super().__init__(name, info, defaults)

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        if self.builder: return self.builder
        super().build(adc_bitwidth, device)
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, sample_mode="timed")
        self.builder.build()
        return self.builder


# Test ###########################################

# ------------------------------------------------
# class: Test
# - Python class corresponding to test objects
#   in regression.json
# ------------------------------------------------

class Test(HashableBase):
    def __init__(self, info, networks, datasets, defaults):
        self.networks = [networks[n] for n in info['networks']]
        self.datasets = [datasets[d] for d in info['datasets']]

        self.description   = info.get('desc', "")
        if 'test_dataset' in info:
            self.test_dataset = [datasets[td] for td in info['test_dataset']] if isinstance(info['test_dataset'], list) else [info['test_dataset']]
        else:
            self.test_dataset = [self.datasets[0]]
        self.skip          = info.get('skip',           False)
        self.learning_rate = info.get('learning_rate',  defaults['learning_rate'])
        self.learning_decay= info.get('learning_decay', defaults['learning_decay'])
        self.max_learn_rate= info.get('max_learn_rate', defaults['max_learn_rate'])
        self.optimizer     = info.get('optimizer',      defaults['optimizer'])
        self.loss          = info.get('loss',           defaults['loss'])
        self.loss_se       = info.get('loss_se',        defaults['loss_se'])
        self.max_epochs    = info.get('max_epochs',     defaults['max_epochs'])
        self.max_accuracy  = info.get('max_accuracy',   defaults['max_accuracy'])
        self.max_loss      = info.get('max_loss',       defaults['max_loss'])
        self.batch_size    = info.get('batch_size',     defaults['batch_size'])
        self.train_split   = info.get('train_split',    defaults['train_split'])
        self.test_split    = 1 - self.train_split if self.train_split != 1 else 1

        #if not isinstance(self.learning_rate, list): self.learning_rate = [self.learning_rate]
        #if not isinstance(self.optimizer,     list): self.optimizer     = [self.optimizer]

    def __copy__(self):
        cls  = type(self)
        that = cls.__new__(cls)
        that.networks = self.networks
        that.datasets = self.datasets
        that.description   = self.description
        that.test_dataset  = self.test_dataset
        that.learning_rate = self.learning_rate
        that.learning_decay= self.learning_decay
        that.max_learn_rate= self.max_learn_rate
        that.optimizer     = self.optimizer
        that.loss          = self.loss
        that.loss_se       = self.loss_se
        that.max_epochs    = self.max_epochs
        that.max_accuracy  = self.max_accuracy
        that.max_loss      = self.max_loss
        that.batch_size    = self.batch_size
        that.train_split   = self.train_split
        that.test_split    = self.test_split
        return that

    def get_csv(self, test_index=0):
        return f"{self.learning_rate},{self.learning_decay},{self.max_learn_rate},{self.optimizer},{self.batch_size},{self.max_epochs},{self.max_accuracy},{self.max_loss},{self.test_dataset[test_index].name},{self.train_split}"

    # --------------------------------------------
    # func: get_optimizer
    # - returns the correct optimizer 
    # - accuracy was intented to be used for cases
    #   where optimizer is changed over time
    #   but this is not currently implemented
    # --------------------------------------------

    def get_optimizer(self, cnn, accuracy=0):
        if self.optimizer == 'Adam':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate, weight_decay=self.learning_decay)

        if self.optimizer == 'Amsgrad':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate, weight_decay=self.learning_decay, amsgrad=True)

        if self.optimizer == 'Adamax':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'SGD':
            return optim.SGD(cnn.parameters(),  lr=self.learning_rate)

        raise NotImplementedError("Unsupported optimizer")

    # --------------------------------------------
    # func: get_loss
    # - returns the correct loss function 
    # --------------------------------------------

    def get_loss(self, network):
        if network.type == 'bitwise':
            return getattr(nn, self.loss)()
        else:
            return getattr(nn, self.loss_se)()

# Regression #####################################

# ------------------------------------------------
# class: Regression
# - python class corresponding to regression 
#   objects in regression.json
# ------------------------------------------------

class Regression:
    def __init__(self, args, overwrite=False, adc_bitwidth=8):
        self.args = args
        self.json = args.json
        self.csv  = f'{args.output}/run_results.csv'
        self.dict = None

        self.adc_bitwidth = adc_bitwidth
        self.overwrite = overwrite
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')

    # --------------------------------------------
    # func: load
    # - reads json file and constructs all python
    #   classes required to represent it
    # --------------------------------------------

    def load(self):
        with open(self.json, "r") as file: 
            self.dict = json.load(file)

        self.defaults = self.dict['defaults']

        self.networks = {name: Network(name, info, self.args) for name, info in self.dict['networks'].items()}
        self.gen_datasets(self.dict['datasets'])
        self.gen_tests(self.dict['tests'])

    # --------------------------------------------
    # func: gen_datasets
    # - Constructs dataset classes from json dict
    # --------------------------------------------

    def gen_datasets(self, dict):
        self.datasets = {}

        for name, info in dict.items():
            if info['type'] == 'sampled' and isinstance(info['sample_mode'], list):
                for mode in info['sample_mode']:
                    inf = info.copy()
                    inf['sample_mode'] = mode
                    nam=f"{name}:{mode.lower()}"
                    self.datasets[nam] = Dataset.from_info(nam, inf, self.defaults)
                inf = info.copy()
                inf['type'] = 'timed'
                nam=f"{name}:tru"
                self.datasets[nam] = Dataset.from_info(nam, inf, self.defaults)
            else:
                self.datasets[name] = Dataset.from_info(name, info, self.defaults)

    # --------------------------------------------
    # func: gen_tests
    # - Constructs tests from json dict
    # --------------------------------------------

    def gen_tests(self, dict):
        self.tests = []

        for info in dict:
            test = Test(info, self.networks, self.datasets, self.defaults)
            if test.skip: continue

            if isinstance(test.learning_rate, list):
                for lr in test.learning_rate:
                    test_i = copy(test)
                    test_i.learning_rate = lr
                    self.tests.append(test_i)
            else:
                self.tests.append(test)

    # --------------------------------------------
    # func: build_datasets
    # - calls dataset.build() for all datsets
    # --------------------------------------------

    def build_datasets(self, *datasets, device=None):
        for d in datasets:
            d.build(adc_bitwidth=self.adc_bitwidth, device=device)

