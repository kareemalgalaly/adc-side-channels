###############################################################################
# File        : /Users/kareemahmad/Projects/SideChannels/adc-side-channel/attack/cnn/regress.py
# Author      : kareemahmad
# Created     : 
# Description : __main__ equivalent. Handles CNN training and testing
###############################################################################

from classes import argparser, Regression, ProgressBar, base36hash
import json

import re
import os
import time

import torch
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 10})
FIGX = 8
FIGY = 8

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
args = argparser.parse_args()

def gradient_hook(module_name, grads):
    def hook(module, grad_in, grad_out):
        grads.extend(grad_in)
    return hook

class CNNRegression(Regression):
    def run_all(self):
        # Header

        if not(self.args.nowrite or self.args.preview):
            if not(os.path.isfile(self.csv)):
                with open(self.csv, "w") as file:
                    file.write("Run ID,Network,Network ID,Network Type,Definition,Inputs,Dataset,Datset ID,")
                    file.write("Type,Path,Dataset Cols,Datset Info,Test ID,Learning Rate,LR Decay,Max LR,")
                    file.write("Optimizer,Batch Size,Max Epochs,Target Accuracy,Target Loss,Test Dataset,Split,")
                    file.write("Bit,Accuracy,Peak Accuracy,Test Accuracy,Loss,Epoch,Runtime,Job Timestamp\n")

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
            if not re.match(args.test, test.description): continue
            for test_dataset in test.test_dataset:
                if test_dataset not in test.datasets:
                    self.build_datasets(test_dataset, device=device)
                    test_dataset.builder.build_dataloaders(test=1, proportion=test.test_split, batch_size=test.batch_size, shuffle=True)

            for dataset in test.datasets:
                self.build_datasets(dataset, device=device)

                for network in test.networks:
                    assert network.inputs == dataset.cols

                    run_hash = base36hash(network.get_csv() + dataset.get_csv() + test.get_csv())
                    print(f"{run_hash},{network.name},{dataset.name},{test}")

                    if not(self.args.preview):
                        fig, axs = plt.subplots(3, figsize=(FIGX,FIGY))
                        fig.suptitle(f"{run_hash}\n{network.name}  -  {dataset.name}  -  {test.optimizer}({test.learning_rate})\n")
                        axs[0].set_title("Loss")
                        axs[1].set_title("Accuracy")
                        axs[2].set_title("Gradient")
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
                                self.run_eval_cnn(test, network, dataset, device, run_hash_i, fig, axs, bit=i)
                        elif network.type == 'single_ended':
                            if run_hash in skip_tests: 
                                print(f"  SKIPPING {run_hash}"); continue
                                skip = True
                            self.run_eval_cnn(test, network, dataset, device, run_hash, fig, axs, bit=-1)
                        else:
                            raise RuntimeError(f"Unsupported network type {network.type}")


                    except KeyboardInterrupt as e:
                        if not(self.args.preview or self.args.nowrite):
                            fig.savefig(f'{self.args.output}/{run_hash}_{job_launch_time}.png')
                            plt.close()
                        print("Keyboard Interrupt detected. Shutting down...")
                        exit()

                    if not(self.args.preview or self.args.nowrite or skip):
                        fig.savefig(f'{self.args.output}/{run_hash}.png')
                        plt.close()

    def run_eval_cnn(self, test, network, dataset, device, run_hash, fig, axs, bit=-1):
        plot_period = 10 if network.predef else 1000 if device else 10
        acc_period  = 1  if network.predef else 100  if device else 10

        start_tm = time.monotonic()
    
        dataset.builder.build_dataloaders(test=0, proportion=test.train_split, batch_size=test.batch_size, shuffle=True)
        dataloader  = dataset.builder.dataloader if bit == -1 else dataset.builder.dataloaders[bit]
        batch_count = -(len(dataset.builder.dataset) // -test.batch_size)
    
        cnn = network.create(dataset.len, dataset.cols)
        bit = "_" if bit == -1 else bit

        single_ended = network.type == 'single_ended'

        #if bit == self.adc_bitwidth-1 or bit == -1: print(cnn)

        if (cnn is None): raise RuntimeError("Failed to build CNN")
        if (self.args.preview): return

        cnn = cnn.to(device)
        grads = []
        for name, layer in cnn.named_modules():
            if any(layer.children()) is False:
                layer.register_full_backward_hook(gradient_hook(name, grads))
    
        loss_arr = torch.empty(test.max_epochs, device=device)
        grad_arr = torch.empty(test.max_epochs//acc_period, device=device)
        acc_arr  = torch.empty(test.max_epochs//acc_period, device=device)
        loss_g = None
        grad_g = None
        acc_g  = None

        criterion = test.get_loss(network)
        optimizer = test.get_optimizer(cnn, accuracy=0)
        #scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=100, factor=0.7)
        scheduler = None
    
        progress = ProgressBar(f_start="Training ", f_end="{model} | Loss {loss:8} | Accuracy {acc:6}:{pacc:6} | Test {tst:6} | {msg}", max_val=test.max_epochs)
        progress.start(model=run_hash, loss=1.0, acc=0.0, pacc=0.0, tst="    --", msg="")

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

                    # grad_arr[acc_indx] = 
                    grd = 0
                    cnt = 0
                    for gt in grads:
                        if gt is not None:
                            grd += gt.abs().sum()
                            cnt += len(gt)
                    grad_arr[acc_indx] = grd / cnt
                    grads.clear()

                if epoch % plot_period == 0:
                    if not self.args.headless:
                        if loss_g: loss_g.remove()
                        if grad_g: grad_g.remove()
                        if acc_g:  acc_g.remove()
                        loss_g = axs[0].plot(loss_arr.detach().cpu()[:epoch], color='gray', linestyle='dotted')[0]
                        acc_g  = axs[1].plot(acc_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                        grad_g = axs[2].plot(grad_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                        # plt.pause(0.01) # update plots and move fig to foreground
                        fig.canvas.flush_events() # update plots without moving window to foreground

                #if accuracy >= test.learning_decay_start:
                #    optimizer = test.get_optimizer(cnn, accuracy)

                if accuracy >= test.max_accuracy:
                    progress.update(epoch, msg=f"Hit Acc {test.max_accuracy}"); break

                if loss <= test.max_loss:
                    progress.update(epoch, msg=f"Hit Loss {test.max_loss}"); break
        except KeyboardInterrupt as e:
            progress.update(epoch, msg="Interrupted  ")
            progress.stop(epoch)
            raise e

        label = f'cnn[{bit}]'
        axs[0].plot(loss_arr.detach().cpu()[:epoch], label=label)
        axs[1].plot(acc_arr.cpu()[:epoch//acc_period+1], label=label)
        axs[2].plot(grad_arr.cpu()[:epoch//acc_period+1], label=label)
        axs[0].legend()
        axs[1].legend()
        axs[2].legend()
        if not self.args.headless:
            # plt.pause(5) # update plots and moves fig to foreground
            fig.canvas.flush_events() # update plots without moving window to foreground

        if self.args.nowrite: return

        stop_tm = time.monotonic()
        runtime = stop_tm - start_tm

        torch.save(cnn.state_dict(), f'{self.args.output}/{run_hash}.state')

        # Find final accuracy on test dataset

        for ti, test_dataset in enumerate(test.test_dataset):
            if test_dataset in test.datasets:
                test_dataset.builder.build_dataloaders(test=1, proportion=test.test_split, batch_size=test.batch_size, shuffle=True)

            dataloader = test_dataset.builder.dataloader if bit == "_" else test_dataset.builder.dataloaders[bit]
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
            test_accuracy = correct / len(test_dataset.builder.dataset)
            progress.update(epoch, tst=round(float(test_accuracy), 4))
            progress.stop(epoch+1)

            with open(self.csv, "a") as file:
                file.write(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test.hash()},{test.get_csv(ti)},{bit},{facc},{pacc},{test_accuracy},{loss},{epoch},{runtime},{job_launch_time}\n")


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

# Main ###########################################

if __name__  == '__main__':
    args = argparser.parse_args()

    if args.seed:
        set_seed(seed)

    if not args.nowrite:
        os.makedirs(args.output, exist_ok=True)

    if args.headless:
        matplotlib.use('Agg') # backend for non-GUI rendering

    regression = CNNRegression(args)
    regression.load()
    for i in range(args.repeat):
        regression.run_all()

