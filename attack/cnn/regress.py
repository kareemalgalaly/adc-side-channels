from dataloader import TraceDatasetBuilder
from cnn_gen import GenericCNN
import json

import os
import sys
import time
import hashlib
import datetime

import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

from copy import copy

import argparse

argparser = argparse.ArgumentParser(prog="regress.py", description="Run cnn regressions")
argparser.add_argument("-i", "--json",   type=str, default='regression.json', help="JSON description of CNNs")
argparser.add_argument("-o", "--output", type=str, default='outputs', help="Directory for output files")
argparser.add_argument("-c", "--cpuonly", const=True, default=False, action='store_const', help="Don't use GPU even if available")
argparser.add_argument("-n", "--nowrite", const=True, default=False, action='store_const', help="Don't write any outputs")
argparser.add_argument("-f", "--force", const=True, default=False, action='store_const', help="Overwrite output files")
argparser.add_argument("-p", "--preview", const=True, default=False, action='store_const', help="Don't run anything only list runs that would occur")

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')

# Fake Args ######################################

class Args:
    def __init__(self, json='regression.json', output='outputs', cpuonly=False, nowrite=False, force=False, preview=False):
        self.json    = json
        self.output  = output
        self.cpuonly = cpuonly
        self.nowrite = nowrite
        self.force   = force
        self.preview = preview

# Helpers ########################################

class ProgressBar:
    def __init__(self, f_start="", f_end="", bar_len=30, bar_chr='X', max_val=1, out=sys.stdout):
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

    def stop(self):
        if not(self.running): return

        print(f"{self.f_start.format(**self.kwargs)}[{self.bar_chr*self.bar_len}] {self.max_val}/{self.max_val} {self.f_end.format(**self.kwargs)}", end='\n', file=self.out, flush=True)

        self.kwargs = {}
        self.running = False

# bar = ProgressBar(f_start="Training {}", max_val=100)
# bar.start(("NN"))
# plt.pause(1)
# bar.update(10)
# plt.pause(1)
# bar.update(30)
# plt.pause(1)
# bar.stop()

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
    o = hashlib.shake_128(string.encode('ascii'))
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

class Network(HashableBase):
    def __init__(self, name, info):
        self.name       = name
        self.definition = info['definition']
        self.type       = info['type']
        self.inputs     = info['inputs']

    def get_csv(self):
        return f"{self.type},{self.definition.replace(',',';')},{self.inputs}"

    def create(self, input_len, input_ch):
        desc = f"{input_len},{input_ch}:{self.definition}"
        try:
            return GenericCNN(desc)
        except Exception as e:
            print("Failed to create:", desc)
            print(e)
            return None

# Dataset ########################################

class Dataset(HashableBase):
    def __init__(self, name, info):
        self.name = name
        self.path = os.path.join(data_dir, info['path'])
        self.type = info['type']
        self.frmt = info['format']
        self.cols = info['columns']

    @classmethod
    def from_info(cls, name, info):
        if info['type'] == 'raw':
            return RawDataset(name, info)
        elif info['type'] == 'timed':
            return TimedDataset(name, info)
        else:
            return SampledDataset(name, info)

    def get_csv(self):
        return f"{self.type},{self.path},{self.cols}"

    def build(self, adc_bitwidth=8, device=None):
        self.builder = TraceDatasetBuilder(adc_bitwidth=adc_bitwidth, cache=True, device=device)
        return self.builder
    
    def get_trace(self, label, index=0, bit=-1):
        dataset = self.builder.dataset if bit == -1 else self.builder.datasets[bit]
        return dataset.get_by_label(label, index=index)


class RawDataset(Dataset):
    def __init__(self, name, info):
        assert info['type'] == 'raw'
        super().__init__(name, info)

        self.len  = info['len']

    def get_csv(self):
        return f"{super().get_csv()},{self.len}"

    def build(self, adc_bitwidth=8, device=None):
        super().build(adc_bitwidth, device)
        self.builder.add_files(self.path, self.frmt)
        self.builder.build()


class SampledDataset(Dataset):
    def __init__(self, name, info):
        assert info['type'] == 'sampled'
        super().__init__(name, info)

        self.mode     =  info['sample_mode']
        self.interval =  info['sample_interval']
        self.duration =  info['sample_duration']
        self.len      = int(self.duration / self.interval)

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        super().build(adc_bitwidth, device)
        self.builder.add_files(self.path, self.frmt, sample_mode=self.mode, sample_int=self.interval, sample_time=self.duration)
        self.builder.build()

class TimedDataset(Dataset):
    def __init__(self, name, info):
        assert info['type'] == 'timed'
        super().__init__(name, info)

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        super().build(adc_bitwidth, device)
        self.builder.add_files(self.path, self.frmt, sample_mode="timed")
        self.builder.build()


# Test ###########################################

class Test(HashableBase):
    def __init__(self, info, networks, datasets, defaults):
        self.networks = [networks[n] for n in info['networks']]
        self.datasets = [datasets[d] for d in info['datasets']]

        self.skip          = info.get('skip',           False)
        self.learning_rate = info.get('learning_rate',  defaults['learning_rate'])
        self.optimizer     = info.get('optimizer',      defaults['optimizer'])
        self.max_epochs    = info.get('max_epochs',     defaults['max_epochs'])
        self.max_accuracy  = info.get('max_accuracy',   defaults['max_accuracy'])
        self.max_loss      = info.get('max_loss',       defaults['max_loss'])
        self.batch_size    = info.get('batch_size',     defaults['batch_size'])

        #if not isinstance(self.learning_rate, list): self.learning_rate = [self.learning_rate]
        #if not isinstance(self.optimizer,     list): self.optimizer     = [self.optimizer]

    def __copy__(self):
        cls  = type(self)
        that = cls.__new__(cls)
        that.networks = self.networks
        that.datasets = self.datasets
        that.learning_rate = self.learning_rate
        that.optimizer     = self.optimizer
        that.max_epochs    = self.max_epochs
        that.max_accuracy  = self.max_accuracy
        that.max_loss      = self.max_loss
        that.batch_size    = self.batch_size
        return that

    def get_csv(self):
        return f"{self.learning_rate},{self.optimizer},{self.batch_size},{self.max_epochs},{self.max_accuracy},{self.max_loss}"

    def get_optimizer(self, cnn):
        if self.optimizer == 'Adam':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'Amsgrad':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate, amsgrad=True)

        if self.optimizer == 'Adamax':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'SGD':
            return optim.SGD(cnn.parameters(), lr=self.learning_rate)

        raise NotImplementedError("Unsupported optimizer")

# Regression #####################################

class Regression:
    def __init__(self, args, overwrite=False, adc_bitwidth=8):
        self.args = args
        self.json = args.json
        self.csv  = f'{args.output}/run_results.csv'
        self.dict = None

        self.adc_bitwidth = adc_bitwidth
        self.overwrite = overwrite
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')

    def load(self):
        with open(self.json, "r") as file: 
            self.dict = json.load(file)

        # print(json.dumps(self.dict, indent=2))

        self.defaults = self.dict['defaults']

        self.networks = {name: Network(name, info) for name, info in self.dict['networks'].items()}
        self.datasets = {name: Dataset.from_info(name, info) for name, info in self.dict['datasets'].items()}
        self.build_tests(self.dict['tests'])

    def build_tests(self, tests):
        self.tests = []

        for info in tests:
            test = Test(info, self.networks, self.datasets, self.defaults)
            if test.skip: continue

            if isinstance(test.learning_rate, list):
                for lr in test.learning_rate:
                    test_i = copy(test)
                    test_i.learning_rate = lr
                    self.tests.append(test_i)
            else:
                self.tests.append(test)

    def build_datasets(self, *datasets, device=None):
        for d in datasets:
            d.build(adc_bitwidth=self.adc_bitwidth, device=device)

    def run_all(self):
        # Header

        if not(self.args.nowrite or self.args.preview):
            if not(os.path.isfile(self.csv)):
                with open(self.csv, "w") as file:
                    file.write("Run ID,Network,Network ID,Network Type,Definition,Inputs,")
                    file.write("Dataset,Datset ID,Type,Path,Dataset Cols,Datset Info,Test ID,")
                    file.write("Learning Rate,Optimizer,Batch Size,Max Epochs,Target Accuracy,")
                    file.write("Target Loss,Bit,Accuracy,Loss,Epoch,Runtime\n")

        # Skipped tests

        skip_tests = set()
        if not(self.args.force):
            if os.path.isfile(self.csv):
                with open(self.csv, "r") as file:
                    file.readline()
                    for line in file.readlines():
                        skip_tests.add(line.partition(",")[0])

        # Device detection

        if self.args.cpuonly:
            device = None
        else:
            device = torch.device("cuda") if torch.cuda.is_available() else None

        # Plotter setup

        if not(self.args.preview): plt.ion()

        # Regression main

        for test in self.tests:
            for dataset in test.datasets:
                self.build_datasets(dataset, device=device)

                for network in test.networks:
                    assert network.inputs == dataset.cols

                    run_hash = base36hash(network.get_csv() + dataset.get_csv() + test.get_csv())
                    print(f"{run_hash},{network.name},{dataset.name},{test}")

                    if not(self.args.preview):
                        fig, axs = plt.subplots(2, figsize=(8,8))
                        fig.suptitle(f"{run_hash}\n{network.name}  -  {dataset.name}  -  {test.optimizer}({test.learning_rate})\n")
                        axs[0].set_title("Loss")
                        axs[1].set_title("Accuracy")
                    else:
                        axs = None
    
                    try:
                        if network.type == 'bitwise':
                            for i in range(self.adc_bitwidth-1, -1, -1):
                                run_hash_i = f"{run_hash}_{i}"
                                if run_hash_i in skip_tests: 
                                    print(f"  SKIPPING {run_hash_i}"); continue
                                self.run_eval_cnn(test, network, dataset, device, run_hash_i, axs, bit=i)
                        else:
                            if run_hash in skip_tests: 
                                print(f"  SKIPPING {run_hash}"); continue
                            self.run_eval_cnn(test, network, dataset, device, run_hash, axs, bit=-1)

                    except KeyboardInterrupt as e:
                        if not(self.args.preview or self.args.nowrite):
                            fig.savefig(f'{self.args.output}/{run_hash}.png')
                            plt.close()
                        print("Keyboard Interrupt detected. Shutting down...")
                        exit()

                    if not(self.args.preview or self.args.nowrite):
                        fig.savefig(f'{self.args.output}/{run_hash}.png')
                        plt.close()


    def run_eval_cnn(self, test, network, dataset, device, run_hash, axs, bit=-1):
        plot_period = 1000 if device else 10
        acc_period  = 100  if device else 10

        start_tm = time.monotonic()
    
        dataset.builder.build_dataloaders(batch_size=test.batch_size, shuffle=True)
        dataloader  = dataset.builder.dataloader if bit == -1 else dataset.builder.dataloaders[bit]
        batch_count = -(len(dataset.builder.dataset) // -test.batch_size)
    
        cnn = network.create(dataset.len, dataset.cols)
        bit = "_" if bit == -1 else bit

        #if bit == self.adc_bitwidth-1 or bit == -1: print(cnn)

        if (cnn is None): raise RuntimeError("Failed to build CNN")
        if (self.args.preview): return

        cnn = cnn.to(device)
    
        loss_arr = torch.empty(test.max_epochs, device=device)
        acc_arr  = torch.empty(test.max_epochs//acc_period, device=device)
        loss_g = None
        acc_g  = None

        criterion = nn.CrossEntropyLoss()
        optimizer = test.get_optimizer(cnn)
    
        progress = ProgressBar(f_start="Training ", f_end="{model} | Loss {loss:8} | Accuracy {acc:8} | {msg}", max_val=test.max_epochs)
        progress.start(model=run_hash, loss=1.0, acc=0.0, msg="          ")

        try:
            for epoch in range(test.max_epochs):
                correct = 0

                for inputs, labels in dataloader:
                    if device:
                        inputs = inputs.cuda()
                        labels = labels.cuda()

                    # Forward

                    optimizer.zero_grad()
                    output = cnn(inputs)

                    # Backward

                    loss = criterion(output, labels)
                    loss.backward()
                    optimizer.step()

                    # Calculate Accuracy

                    if (epoch % acc_period) == 0:
                        _, predicted = torch.max(output, 1)
                        correct += (predicted == labels).sum()

                loss_arr[epoch] = loss

                if epoch % acc_period == 0:
                    accuracy = correct / len(dataset.builder.dataset)
                    acc_indx = epoch//acc_period
                    acc_arr[acc_indx] = accuracy

                if epoch % plot_period == 0:
                    #print(f'TRAINING: {run_hash}, Epoch {epoch:5}, Loss:     {loss.item()}')
                    #print(f'TRAINING: {run_hash}, Epoch {epoch:5}, Accuracy: {accuracy}')
                    progress.update(epoch, loss=round(loss.item(), 6), acc=round(float(accuracy),6))

                    if loss_g: loss_g.remove()
                    if acc_g:  acc_g.remove()
                    loss_g = axs[0].plot(loss_arr.detach().cpu()[:epoch], color='gray', linestyle='dotted')[0]
                    acc_g  = axs[1].plot(acc_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                    plt.pause(0.01)

                if accuracy >= test.max_accuracy:
                    progress.update(epoch, msg="Reached target accuracy"); break

                if loss <= test.max_loss:
                    progress.update(epoch, msg="Reached target loss"); break
        except KeyboardInterrupt as e:
            progress.update(1,msg="Job Interrupted")
            progress.stop()
            raise e

        progress.stop()

        label = f'cnn[{bit}]'
        axs[0].plot(loss_arr.detach().cpu()[:epoch], label=label)
        axs[1].plot(acc_arr.cpu()[:epoch//acc_period+1], label=label)
        axs[0].legend()
        axs[1].legend()
        plt.pause(0.01)

        if self.args.nowrite: return

        stop_tm = time.monotonic()
        runtime = stop_tm - start_tm

        torch.save(cnn.state_dict(), f'{self.args.output}/{run_hash}.state')

        with open(self.csv, "a") as file:
            file.write(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test},{bit},{accuracy},{loss},{epoch},{runtime}\n")

# Main ###########################################

if __name__  == '__main__':
    args = argparser.parse_args()

    if not args.nowrite:
        os.makedirs(args.output, exist_ok=True)

    regression = Regression(args)
    regression.load()
    regression.run_all()

