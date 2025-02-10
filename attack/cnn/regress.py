from dataloader import TraceDatasetBuilder
from cnn_gen import GenericCNN
import json
#import pprint

import os
import sys
import time
import hashlib
import datetime

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from copy import copy

import argparse

DTYPE = np.float32

argparser = argparse.ArgumentParser(prog="regress.py", description="Run cnn regressions")
argparser.add_argument("-i", "--json",   type=str, default='regression.json', help="JSON description of CNNs")
argparser.add_argument("-o", "--output", type=str, default='outputs', help="Directory for output files")
argparser.add_argument("-c", "--cpuonly", const=True, default=False, action='store_const', help="Don't use GPU even if available")
argparser.add_argument("-n", "--nowrite", const=True, default=False, action='store_const', help="Don't write any outputs")
argparser.add_argument("-f", "--force", const=True, default=False, action='store_const', help="Overwrite output files")
argparser.add_argument("-p", "--preview", const=True, default=False, action='store_const', help="Don't run anything only list runs that would occur")
argparser.add_argument("-x", "--headless", const=True, default=False, action='store_const', help="Do not open any gui's")
argparser.add_argument("--nndebug", const=True, default=False, action='store_const', help="Print information about cnn creation.")

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')

# Fake Args ######################################

class Args:
    def __init__(self, json='regression.json', output='outputs', cpuonly=False, nowrite=False, force=False, preview=False, headless=False):
        self.json    = json
        self.output  = output
        self.cpuonly = cpuonly
        self.nowrite = nowrite
        self.force   = force
        self.preview = preview
        self.headless = headless

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

    def stop(self, value=-1):
        if not(self.running): return
        if value == -1: value = self.max_val

        print(f"{self.f_start.format(**self.kwargs)}[{self.bar_chr*self.bar_len}] {value:{self.val_len}}/{self.max_val} {self.f_end.format(**self.kwargs)}", end='\n', file=self.out, flush=True)

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
        self.outputs    = info['outputs']
        self.weights    = info.get('weights', None)
        self.predef     = self.definition.startswith("predef::")
        self.preprocess = eval(f"lambda x: {info.get('preprocess', 'x')}")

    def get_csv(self):
        return f"{self.type},{self.definition.replace(',',';')},{self.inputs}"

    def create(self, input_len, input_ch):
        if self.predef:
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
                return GenericCNN(desc, debug=args.nndebug)
            except Exception as e:
                print("Failed to create:", desc)
                print(e)
                return None

# Dataset ########################################

class Dataset(HashableBase):
    def __init__(self, name, info):
        self.name = name
        self.type = info['type']
        self.frmt = info['format']
        self.cols = info['columns']
        self.lbls = info.get('labels', 1)
        self.lblf = eval(info.get('label', 'lambda gs:int(gs[0])'), globals(), {})
        self.paths = [os.path.join(data_dir, path) for path in info.get('paths', [])]
        if path := info.get('path', None):
            self.paths.append(os.path.join(data_dir, path))

    @classmethod
    def from_info(cls, name, info):
        if info['type'] == 'raw':
            return RawDataset(name, info)
        elif info['type'] == 'timed':
            return TimedDataset(name, info)
        else:
            return SampledDataset(name, info)

    def get_csv(self):
        return f"{self.type},{';'.join(self.paths)},{self.cols}"

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
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, max_sample=self.len)
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
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, sample_mode=self.mode, sample_int=self.interval, sample_time=self.duration)
        self.builder.build()

class TimedDataset(Dataset):
    def __init__(self, name, info):
        assert info['type'] == 'timed'
        super().__init__(name, info)

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        super().build(adc_bitwidth, device)
        for path in self.paths:
            self.builder.add_files(path, self.frmt, label_func=self.lblf, sample_mode="timed")
        self.builder.build()


# Test ###########################################

class Test(HashableBase):
    def __init__(self, info, networks, datasets, defaults):
        self.networks = [networks[n] for n in info['networks']]
        self.datasets = [datasets[d] for d in info['datasets']]

        self.test_dataset  = datasets[info['test_dataset']] if 'test_dataset' in info else self.datasets[0]
        self.skip          = info.get('skip',           False)
        self.learning_rate = info.get('learning_rate',  defaults['learning_rate'])
        self.max_learn_rate= info.get('max_learn_rate', defaults['max_learn_rate'])
        self.optimizer     = info.get('optimizer',      defaults['optimizer'])
        self.loss          = info.get('loss',           defaults['loss'])
        self.loss_se       = info.get('loss_se',        defaults['loss_se'])
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
        that.test_dataset  = self.test_dataset
        that.learning_rate = self.learning_rate
        that.max_learn_rate= self.max_learn_rate
        that.optimizer     = self.optimizer
        that.loss          = self.loss
        that.loss_se       = self.loss_se
        that.max_epochs    = self.max_epochs
        that.max_accuracy  = self.max_accuracy
        that.max_loss      = self.max_loss
        that.batch_size    = self.batch_size
        return that

    def get_csv(self):
        return f"{self.learning_rate},{self.max_learn_rate},{self.optimizer},{self.batch_size},{self.max_epochs},{self.max_accuracy},{self.max_loss}"

    def get_optimizer(self, cnn):
        if self.optimizer == 'Adam':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'Amsgrad':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate, amsgrad=True)

        if self.optimizer == 'Adamax':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'SGD':
            return optim.SGD(cnn.parameters(),  lr=self.learning_rate)

        raise NotImplementedError("Unsupported optimizer")

    def get_loss(self, network):
        if network.type == 'bitwise':
            return getattr(nn, self.loss)()
        else:
            return getattr(nn, self.loss_se)()

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

        self.defaults = self.dict['defaults']

        self.networks = {name: Network(name, info) for name, info in self.dict['networks'].items()}
        self.gen_datasets(self.dict['datasets'])
        self.gen_tests(self.dict['tests'])

    def gen_datasets(self, dict):
        self.datasets = {}

        for name, info in dict.items():
            if info['type'] == 'sampled' and isinstance(info['sample_mode'], list):
                for mode in info['sample_mode']:
                    inf = info.copy()
                    inf['sample_mode'] = mode
                    nam=f"{name}:{mode.lower()}"
                    self.datasets[nam] = Dataset.from_info(nam, inf)
                inf = info.copy()
                inf['type'] = 'timed'
                nam=f"{name}:tru"
                self.datasets[nam] = Dataset.from_info(nam, inf)
            else:
                self.datasets[name] = Dataset.from_info(name, info)

        #pprint.pprint(self.datasets)

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

    def build_datasets(self, *datasets, device=None):
        seen = set()
        for d in datasets:
            if d not in seen:
                seen.add(d)
                d.build(adc_bitwidth=self.adc_bitwidth, device=device)

    def run_all(self):
        # Header

        if not(self.args.nowrite or self.args.preview):
            if not(os.path.isfile(self.csv)):
                with open(self.csv, "w") as file:
                    file.write("Run ID,Network,Network ID,Network Type,Definition,Inputs,")
                    file.write("Dataset,Datset ID,Type,Path,Dataset Cols,Datset Info,Test ID,")
                    file.write("Learning Rate,Max LR,Optimizer,Batch Size,Max Epochs,Target Accuracy,")
                    file.write("Target Loss,Bit,Accuracy,Peak Accuracy,Test Accuracy,Loss,Epoch,Runtime\n")

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

        if not(self.args.preview or self.args.headless): plt.ion()

        # Regression main

        for test in self.tests:
            if test.test_dataset is not test.datasets[0]:
                self.build_datasets(test.test_dataset, device=device)
                test.test_dataset.builder.build_dataloaders(batch_size=test.batch_size, shuffle=True)

            for dataset in test.datasets:
                self.build_datasets(dataset, device=device)

                for network in test.networks:
                    assert network.inputs  == dataset.cols, f"network.inputs {network.inputs} != dataset.cols {dataset.cols}"
                    assert network.outputs == dataset.lbls, f"network.outputs {network.outputs} != dataset.lbls {dataset.lbls}"

                    run_hash = base36hash(network.get_csv() + dataset.get_csv() + test.get_csv())
                    print(f"{run_hash},{network.name},{dataset.name},{test}")

                    if not(self.args.preview):
                        fig, axs = plt.subplots(2, figsize=(8,8))
                        fig.suptitle(f"{run_hash}\n{network.name}  -  {dataset.name}  -  {test.optimizer}({test.learning_rate})\n")
                        axs[0].set_title("Loss")
                        axs[1].set_title("Accuracy")
                    else:
                        axs = None
    
                    skip = False
                    try:
                        if network.type == 'bitwise':
                            for i in range(self.adc_bitwidth-1, -1, -1):
                                run_hash_i = f"{run_hash}_{i}"
                                if run_hash_i in skip_tests: 
                                    print(f"  SKIPPING {run_hash_i}"); continue
                                    skip = True
                                self.run_eval_cnn(test, network, dataset, device, run_hash_i, axs, bit=i)
                        elif network.type == 'single_ended':
                            if run_hash in skip_tests: 
                                print(f"  SKIPPING {run_hash}"); continue
                                skip = True
                            self.run_eval_cnn(test, network, dataset, device, run_hash, axs, bit=-1)
                        else:
                            raise RuntimeError(f"Unsupported network type {network.type}")


                    except KeyboardInterrupt as e:
                        if not(self.args.preview or self.args.nowrite):
                            fig.savefig(f'{self.args.output}/{run_hash}.png')
                            plt.close()
                        print("Keyboard Interrupt detected. Shutting down...")
                        exit()

                    if not(self.args.preview or self.args.nowrite or skip):
                        fig.savefig(f'{self.args.output}/{run_hash}.png')
                        plt.close()

    def run_eval_cnn(self, test, network, dataset, device, run_hash, axs, bit=-1):
        plot_period = 1 if network.predef else 1000 if device else 10
        acc_period  = 1 if network.predef else 100  if device else 10

        start_tm = time.monotonic()
    
        dataset.builder.build_dataloaders(batch_size=test.batch_size, shuffle=True)
        dataloader  = dataset.builder.dataloader if bit == -1 else dataset.builder.dataloaders[bit]
        batch_count = -(len(dataset.builder.dataset) // -test.batch_size)
    
        cnn = network.create(dataset.len, dataset.cols)
        bit = "_" if bit == -1 else bit

        single_ended = network.type == 'single_ended'

        #if bit == self.adc_bitwidth-1 or bit == -1: print(cnn)

        if (cnn is None): raise RuntimeError("Failed to build CNN")
        if (self.args.preview): return

        cnn = cnn.to(device)
    
        loss_arr = torch.empty(test.max_epochs, device=device)
        acc_arr  = torch.empty(test.max_epochs//acc_period, device=device)
        loss_g = None
        acc_g  = None

        criterion = test.get_loss(network) #nn.CrossEntropyLoss()
        optimizer = test.get_optimizer(cnn)
        #scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=100, factor=0.7)
        scheduler = None
    
        progress = ProgressBar(f_start="Training ", f_end="{model} | Loss {loss:8} | Accuracy {acc:6}:{pacc:6} | Test {tst:8} | {msg}", max_val=test.max_epochs)
        progress.start(model=run_hash, loss=1.0, acc=0.0, pacc=0.0, tst=0.0, msg="")

        pacc = 0 # peak_accuracy

        try:
            for epoch in range(test.max_epochs):
                correct = 0

                for inputs, labels in dataloader:
                    if device:
                        inputs = inputs.cuda()
                        labels = labels.cuda()

                    inputs = network.preprocess(inputs)

                    # Forward

                    optimizer.zero_grad()
                    output = cnn(inputs)

                    # Backward

                    if single_ended: labels = labels.reshape(output.shape)
                    #print(output)
                    #print(labels)
                    loss = criterion(output, labels)
                    loss.backward()
                    optimizer.step()
                    if scheduler: scheduler.step(loss)

                    # Calculate Accuracy

                    if (epoch % acc_period) == 0:
                        if single_ended:
                            correct += (output.round() == labels.round()).sum()
                        else:
                            _, predicted = torch.max(output, 1)
                            correct += (predicted == labels).sum()

                loss_arr[epoch] = loss

                if epoch % acc_period == 0:
                    accuracy = correct / len(dataset.builder.dataset)
                    acc_indx = epoch//acc_period
                    acc_arr[acc_indx] = accuracy
                    facc = float(accuracy)
                    pacc = max(facc, pacc)
                    progress.update(epoch, loss=round(loss.item(), 6), acc=round(facc,4), pacc=round(pacc,4))

                if epoch % plot_period == 0:
                    if not self.args.headless:
                        if loss_g: loss_g.remove()
                        if acc_g:  acc_g.remove()
                        loss_g = axs[0].plot(loss_arr.detach().cpu()[:epoch], color='gray', linestyle='dotted')[0]
                        acc_g  = axs[1].plot(acc_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                        plt.pause(0.01)

                if accuracy >= test.max_accuracy:
                    progress.update(epoch, msg=f"Target acc reached {test.max_accuracy}"); break

                if loss <= test.max_loss:
                    progress.update(epoch, msg=f"Target loss reached {test.max_loss}"); break
        except KeyboardInterrupt as e:
            progress.update(epoch, msg="Job Interrupted")
            progress.stop(epoch)
            raise e

        label = f'cnn[{bit}]'
        axs[0].plot(loss_arr.detach().cpu()[:epoch], label=label)
        axs[1].plot(acc_arr.cpu()[:epoch//acc_period+1], label=label)
        axs[0].legend()
        axs[1].legend()
        if not self.args.headless:
            plt.pause(5)

        if self.args.nowrite: return

        stop_tm = time.monotonic()
        runtime = stop_tm - start_tm

        torch.save(cnn.state_dict(), f'{self.args.output}/{run_hash}.state')

        # Find final accuracy on test dataset

        dataloader = test.test_dataset.builder.dataloader if bit == "_" else test.test_dataset.builder.dataloaders[bit]
        correct = 0
        for inputs, labels in dataloader:
            if device:
                inputs = inputs.cuda()
                labels = labels.cuda()

            inputs = network.preprocess(inputs)

            # Forward

            optimizer.zero_grad()
            output = cnn(inputs)

            if single_ended:
                labels = labels.reshape(output.shape)
                correct += (output.round() == labels.round()).sum()
            else:
                _, predicted = torch.max(output, 1)
                correct += (predicted == labels).sum()
        test_accuracy = correct / len(test.test_dataset.builder.dataset)
        progress.update(epoch, tst=round(float(test_accuracy), 6))
        progress.stop(epoch+1)

        with open(self.csv, "a") as file:
            file.write(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test},{bit},{accuracy},{test_accuracy},{loss},{epoch},{runtime}\n")

# Main ###########################################

if __name__  == '__main__':
    args = argparser.parse_args()

    if not args.nowrite:
        os.makedirs(args.output, exist_ok=True)

    if args.headless:
        matplotlib.use('Agg') # backend for non-GUI rendering

    regression = Regression(args)
    regression.load()
    regression.run_all()

