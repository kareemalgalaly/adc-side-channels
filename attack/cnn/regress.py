###############################################################################
# File        : attack/cnn/regress.py
# Author      : kareemahmad
# Created     : 
# Description : __main__ equivalent. Handles CNN training and testing
###############################################################################

from classes import argparser, Regression
from utils import ProgressBar, base36hash
import json

import re
import os
import time
import random

import torch
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 10})
FIGX = 8
FIGY = 3.5

#job_launch_time = time.ctime()
job_launch_time = time.strftime("%y%m%d_%H%M")

argparser.add_argument("-c", "--cpuonly", const=True, default=False, action='store_const', help="Don't use GPU even if available")
argparser.add_argument("-n", "--nowrite", const=True, default=False, action='store_const', help="Don't write any outputs")
argparser.add_argument("-f", "--force", const=True, default=False, action='store_const', help="Overwrite output files")
argparser.add_argument("-p", "--preview", const=True, default=False, action='store_const', help="Don't run anything only list runs that would occur")
argparser.add_argument("-x", "--headless", const=True, default=False, action='store_const', help="Do not open any gui's")
argparser.add_argument("-t", "--test", type=str, default="", help="Limit run tests to those whose description matches the specified regex")
argparser.add_argument("-r", "--repeat", type=int, default=1, help="Rerun training/test this many times. requires -f flag to work properly")
argparser.add_argument("--nndebug", const=True, default=False, action='store_const', help="Print information about cnn creation.")
argparser.add_argument("--seed", type=int, default=None, help="Override random seed")
argparser.add_argument("--gradplot", action="store_true", help="Plot gradient")
argparser.add_argument("--testplot", action="store_true", help="Plot test accuracy")
argparser.add_argument("--fineplot", action="store_true", help="Plot metrics finely")
args = argparser.parse_args()

def gradient_hook(module_name, grads):
    def hook(module, grad_in, grad_out):
        grads.extend(grad_in)
    return hook

class CNNRegression(Regression):
    def __init__(self, args, seed, overwrite=False, adc_bitwidth=8):
        super().__init__(args, overwrite=overwrite, adc_bitwidth=adc_bitwidth)

        self.seed = seed

        self.skip_tests = set()
        self.device = None
        self.axs = None

    def main(self):
        self.write_header()
        self.filter_tests()
        self.get_device()

        for test in self.tests:
            if test is None: 
                if not self.args.seed:
                    self.seed = int.from_bytes(os.urandom(4))
                    print("Running with seed:", self.seed)
                continue

            self.prepare_datasets(test)

            for dataset in test.datasets:
                self.retrain_datacache(test, dataset)

                for network in test.networks:
                    assert network.inputs == dataset.cols

                    run_hash = base36hash(network.get_csv() + dataset.get_csv() + test.get_csv())
                    print(f"{run_hash},{network.name},{dataset.name},{test}")

                    self.prepare_figure(f"{run_hash} ({self.seed})\n{network.name}  -  {dataset.name}  -  {test.optimizer}({test.learning_rate})\n")
                    skip = True
    
                    try:
                        match network.type:
                            case 'bitwise':
                                for i in range(self.adc_bitwidth-1, -1, -1):
                                    skip &= self.run_single_test(test, network, dataset, f"{run_hash}_{i}", bit=i)

                            case 'single_ended':
                                skip &= self.run_single_test(test, network, dataset, run_hash, bit=-1)

                            case _:
                                raise RuntimeError(f"Unsupported network type {network.type}")


                    except KeyboardInterrupt as e:
                        print("Keyboard Interrupt detected. Shutting down...")
                        if not(self.args.preview or self.args.nowrite):
                            self.fig.savefig(f'{self.args.output}/{run_hash}_{job_launch_time}.png')
                            plt.close()
                        exit()

                    if not(self.args.preview or self.args.nowrite or skip):
                        self.fig.savefig(f'{self.args.output}/{run_hash}:{self.seed}.png')
                        plt.close()

    # --------------------------------------------
    # func: write_header
    # - writes the header for the csv
    # --------------------------------------------

    def write_header(self):
        if not(self.args.nowrite or self.args.preview):
            if not(os.path.isfile(self.csv)):
                with open(self.csv, "w") as file:
                    file.write("Run ID,Network,Network ID,Network Type,Definition,Inputs,Dataset,Datset ID,")
                    file.write("Type,Path,Dataset Cols,Format,Normalizer,Datset Info,Test ID,Learning Rate,LR Decay,Max LR,")
                    file.write("Optimizer,Batch Size,Max Epochs,Target Accuracy,Target Loss,Test Dataset,Split,")
                    file.write("Bit,Accuracy,Peak Accuracy,Test Accuracy,Loss,Epoch,Runtime,Job Timestamp,Seed\n")

    # --------------------------------------------
    # func: filter_tests
    # - builds list of tests that were previously run
    # - filters out tests not matching args.test
    # - applies args.repeat if applicable
    # --------------------------------------------

    def filter_tests(self):
        self.skip_tests = set()

        if not self.args.force: 
            if os.path.isfile(self.csv):
                with open(self.csv, "r") as file:
                    file.readline()
                    for line in file.readlines():
                        self.skip_tests.add(line.partition(",")[0])

        self.tests = [t for t in self.tests if re.match(args.test, t.description)]
        if self.args.repeat > 1:
            self.tests.append(None)
            self.tests *= self.args.repeat

    # --------------------------------------------
    # func: get_device
    # - Detects if cuda is available
    # --------------------------------------------

    def get_device(self):
        if not self.args.cpuonly:
            self.device = torch.device("cuda") if torch.cuda.is_available() else None

    # --------------------------------------------
    # func: prepare_datasets
    # - prepares the datasets and dataloaders 
    #   for a given test
    # --------------------------------------------

    def prepare_datasets(self, test):
        all_datasets = set(test.test_dataset) | set(test.datasets)
        for dataset in all_datasets:
            self.build_datasets(dataset, device=self.device)
            batch_size = test.batch_size if test.batch_size != -1 else len(dataset.builder)
            dataset.builder.build_dataloaders(proportion=test.test_split, batch_size=batch_size, shuffle=True)

    # --------------------------------------------
    # func: retrain_datacache
    # - trains dataset cache against the training 
    #   dataset (pre-normalization)
    # --------------------------------------------

    def retrain_datacache(self, test, dataset):
        dataset.builder.cache.retrain()
        for test_dataset in test.test_dataset:
            if test_dataset is not dataset:
                test_dataset.builder.cache.retrain(dataset.builder.cache)

    # --------------------------------------------
    # func: prepare_figure
    # - constructs the figure for plotting
    # --------------------------------------------

    def prepare_figure(self, title):
        if self.args.preview:
            return

        labels = ["Loss", "Accuracy"]

        if self.args.testplot: labels.append("Test Accuracy")
        if self.args.gradplot: labels.append("Gradient")

        fig, axs = plt.subplots(len(labels), figsize=(FIGX,FIGY*len(labels)))
        for i, l in enumerate(labels): axs[i].set_title(l)

        fig.suptitle(title)
        self.axs = axs
        self.fig = fig

    def run_single_test(self, test, network, dataset, run_hash, bit=-1):
        if (self.args.preview): return True
        if run_hash in self.skip_tests: 
            print(f"  SKIPPING {run_hash}"); return True


        ## Basic parameters --------------------------------

        plot_period = 10 if self.args.fineplot else 100 if self.device else 10
        acc_period  = 1  if self.args.fineplot else 100 if self.device else 10

        self.set_seed()
        start_tm = time.monotonic()
        se = network.type == 'single_ended'
        test_builder = [td.builder for td in test.test_dataset if td is not dataset]
        test_builder = test_builder[0] if test_builder else dataset.builder

        if bit == -1:
            dataloader = dataset.builder.dataloader
            test_dataloader = test_builder.dataloader
            bit = "_"
        else:
            dataloader = dataset.builder.dataloaders[bit]
            test_dataloader = test_builder.dataloaders[bit]


        ## Build CNN ---------------------------------------

        if cnn := network.create(dataset.len, dataset.cols):
            cnn = cnn.to(self.device)
        else:
            raise RuntimeError("Failed to build CNN")

        criterion = test.get_loss(network)
        optimizer = test.get_optimizer(cnn, accuracy=0)
        #scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=100, factor=0.7)
        scheduler = None

    
        ## Plotting Arrays --------------------------------- 

        loss_arr = torch.empty(test.max_epochs, device=self.device)
        acc_arr  = torch.empty(test.max_epochs//acc_period, device=self.device)
        loss_g = None
        acc_g  = None

        if self.args.testplot:
            test_arr = torch.empty(test.max_epochs//acc_period, device=self.device)
            test_g = None

        if self.args.gradplot:
            grads = []
            for name, layer in cnn.named_modules():
                if any(layer.children()) is False:
                    layer.register_full_backward_hook(gradient_hook(name, grads))
            grad_arr = torch.empty(test.max_epochs//acc_period, device=self.device)
            grad_g = None

        progress = ProgressBar(f_start="Training ", f_end="{model} | Loss {loss:7} | Acc {acc:5}:{pacc:5} | Test {tst:5} | {msg}", max_val=test.max_epochs)
        progress.start(model=run_hash, loss=1.0, acc=0.0, pacc=0.0, tst="    --", msg="")

        pacc = 0 # peak_accuracy

        
        ## Train -------------------------------------------

        try:
            for epoch in range(test.max_epochs):
                calc_metrics = epoch % acc_period == 0
                plot_metrics = epoch % plot_period == 0

                loss, accuracy = self.do_nn_pass(network, dataloader, cnn, optimizer, criterion, scheduler, se, True, calc_metrics)
                loss_arr[epoch] = loss

                if calc_metrics:
                    # accuracy = float(correct / len(dataset.builder.dataset))
                    acc_indx = epoch // acc_period
                    acc_arr[acc_indx] = accuracy
                    facc = float(accuracy)
                    pacc = max(facc, pacc)

                    if self.args.testplot:
                        test_builder.set_test()
                        l, a = self.do_nn_pass(network, test_dataloader, cnn, optimizer, criterion, scheduler, se, False, True)
                        test_arr[acc_indx] = a
                        test_builder.set_train()

                    if self.args.gradplot:
                        grd = 0
                        cnt = 0
                        for gt in grads:
                            if gt is not None:
                                grd += gt.abs().sum()
                                cnt += len(gt)
                        grad_arr[acc_indx] = grd / cnt
                        grads.clear()

                    progress.update(epoch, loss=round(loss.item(), 6), acc=round(facc,4), pacc=round(pacc,4))

                if plot_metrics:
                    if not self.args.headless:
                        if loss_g: loss_g.remove()
                        loss_g = self.axs[0].plot(loss_arr.detach().cpu()[:epoch], color='gray', linestyle='dotted')[0]

                        if acc_g:  acc_g.remove()
                        acc_g  = self.axs[1].plot(acc_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                        i = 2

                        if self.args.testplot:
                            if test_g: test_g.remove()
                            test_g = self.axs[i].plot(test_arr.cpu()[:acc_indx+1], color='gray', linestyle='dotted')[0]
                            i += 1

                        if self.args.gradplot:
                            if grad_g: grad_g.remove()
                            grad_g = self.axs[i].plot(grad_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                            i += 1

                        self.fig.canvas.flush_events() # update plots without moving window to foreground

                if calc_metrics and (accuracy >= test.max_accuracy):
                    progress.update(epoch, msg=f"Hit Acc {test.max_accuracy}"); break

                if loss <= test.max_loss:
                    progress.update(epoch, msg=f"Hit Loss {test.max_loss}"); break

        except KeyboardInterrupt as e:
            progress.update(epoch, msg="Interrupted  ")
            progress.stop(epoch)
            raise e


        ## Plot Training Metrics ---------------------------

        label = f'cnn[{bit}]'

        if loss_g: loss_g.remove()
        self.axs[0].plot(loss_arr.detach().cpu()[:epoch], label=label)
        self.axs[0].legend()

        if acc_g: acc_g.remove()
        self.axs[1].plot(acc_arr.cpu()[:epoch//acc_period+1], label=label)
        self.axs[1].legend()

        i = 2

        if self.args.testplot:
            if test_g: test_g.remove()
            self.axs[i].plot(test_arr.cpu()[:epoch//acc_period+1], label=label)
            self.axs[i].legend()
            i += 1

        if self.args.gradplot:
            if grad_g: grad_g.remove()
            self.axs[i].plot(grad_arr.cpu()[:epoch//acc_period+1], label=label)
            self.axs[i].legend()
            i += 1

        if not self.args.headless:
            self.fig.canvas.flush_events() # update plots without moving window to foreground

        if self.args.nowrite: return False


        ## Write Training Results --------------------------

        stop_tm = time.monotonic()
        runtime = stop_tm - start_tm

        torch.save(cnn.state_dict(), f'{self.args.output}/{run_hash}.state')

        # Find final accuracy on test dataset

        for ti, test_dataset in enumerate(test.test_dataset):
            test_dataset.builder.set_test()
            test_dataloader = test_dataset.builder.dataloader if bit == "_" else test_dataset.builder.dataloaders[bit]

            l, test_accuracy = self.do_nn_pass(network, test_dataloader, cnn, optimizer, criterion, scheduler, se, False, True)
            progress.update(epoch, tst=round(float(test_accuracy), 4))
            progress.stop(epoch+1)

            with open(self.csv, "a") as file:
                file.write(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test.hash()},{test.get_csv(ti)},{bit},{facc},{pacc},{test_accuracy},{loss},{epoch},{runtime},{job_launch_time},{seed}\n")

        return False

    def do_nn_pass(self, network, dataloader, cnn, optimizer, criterion, scheduler, se, do_backward, do_accuracy):
        correct = 0
        count   = 0
        loss = None

        for inputs, labels in dataloader:
            if self.device:
                inputs = inputs.cuda()
                labels = labels.cuda()

            inputs = network.preprocess(inputs)

            # Forward

            optimizer.zero_grad()
            output = cnn(inputs)

            # Backward

            if do_backward:
                if se: labels = labels.reshape(output.shape)
                loss = criterion(output, labels)
                loss.backward()
                optimizer.step()
                if scheduler: scheduler.step(loss)

            # Calculate Accuracy

            if do_accuracy:
                count += len(output)
                if se:
                    labels = labels.reshape(output.shape)
                    correct += (output.round() == labels.round()).sum()
                else:
                    _, predicted = torch.max(output, 1)
                    correct += (predicted == labels).sum()

        if do_accuracy:
            return loss, correct / count 

        return loss, 0

    def set_seed(self):
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

# Main ###########################################

if __name__  == '__main__':
    args = argparser.parse_args()
    seed = args.seed if args.seed else int.from_bytes(os.urandom(4))

    print("Running with seed:", seed)

    if not args.nowrite:
        os.makedirs(args.output, exist_ok=True)

    if args.headless:
        matplotlib.use('Agg') # backend for non-GUI rendering

    if not(args.preview or args.headless):
        plt.ion()

    regression = CNNRegression(args, seed)
    regression.load()
    regression.main()

