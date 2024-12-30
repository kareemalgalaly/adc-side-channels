from dataloader import TraceDatasetBuilder
from cnn_gen import GenericCNN
import json

import os
import time
import datetime

import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')

# Base ###########################################

base36char = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def base36(number):
    result = ""
    number = abs(number)

    while number != 0:
        number, remainder = divmod(number, 36)
        result += base36char[remainder]

    return result or base36char[0]

class HashableBase:
    def __str__(self):
        csv = self.get_csv()
        return f"{base36(hash(csv))},{csv}"

    def __hash__(self):
        return hash(self.get_csv())

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
        return f"{self.type},{self.definition},{self.inputs}"

    def create(self, input_len, input_ch):
        return GenericCNN(f"{input_len},{input_ch}:{self.definition}")

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
        else:
            return SampledDataset(name, info)

    def get_csv(self):
        return f"{self.type},{self.path},{self.cols}"

    def build(self, adc_bitwidth=8, device=None):
        self.builder = TraceDatasetBuilder(adc_bitwidth=adc_bitwidth, cache=True, device=device)
        return self.builder


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
        self.len      = self.duration / self.interval

    def get_csv(self):
        return f"{super().get_csv()},{self.mode};{self.interval};{self.duration}"

    def build(self, adc_bitwidth=8, device=None):
        super().build(adc_bitwidth, device)
        self.builder.add_files(self.path, self.frmt, sample_mode=self.mode, sample_int=self.interval, sample_time=self.duration)
        self.builder.build()


# Test ###########################################

class Test(HashableBase):
    def __init__(self, info, networks, datasets, defaults):
        self.networks = [networks[n] for n in info['networks']]
        self.datasets = [datasets[d] for d in info['datasets']]

        self.learning_rate = info.get('learning_rate',  defaults['learning_rate'])
        self.optimizer     = info.get('optimizer',      defaults['optimizer'])
        self.max_epochs    = info.get('max_epochs',     defaults['max_epochs'])
        self.max_accuracy  = info.get('max_accuracy',   defaults['max_accuracy'])
        self.max_loss      = info.get('max_loss',       defaults['max_loss'])
        self.batch_size    = info.get('batch_size',     defaults['batch_size'])

        #if not isinstance(self.learning_rate, list): self.learning_rate = [self.learning_rate]
        #if not isinstance(self.optimizer,     list): self.optimizer     = [self.optimizer]

    def get_csv(self):
        return f"{self.learning_rate},{self.optimizer},{self.batch_size}.{self.max_epochs},{self.max_accuracy},{self.max_loss}"

    def get_optimizer(self, cnn):
        if self.optimizer == 'Adam':
            return optim.Adam(cnn.parameters(), lr=self.learning_rate)

        if self.optimizer == 'SGD':
            return optim.SGD(cnn.parameters(), lr=self.learning_rate)

        raise NotImplementedError("Unsupported optimizer")

# Regression #####################################

class Regression:
    def __init__(self, path, overwrite=False, adc_bitwidth=8):
        self.path = path
        self.dict = None

        self.adc_bitwidth = adc_bitwidth
        self.overwrite = overwrite
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')

    def load(self):
        with open(self.path, "r") as file: 
            self.dict = json.load(file)

        print(json.dumps(self.dict, indent=2))

        self.defaults = self.dict['defaults']

        self.networks = {name: Network(name, info) for name, info in self.dict['networks'].items()}
        self.datasets = {name: Dataset.from_info(name, info) for name, info in self.dict['datasets'].items()}
        self.tests =    [Test(info, self.networks, self.datasets, self.defaults) for info in self.dict['tests']]

    def run_all(self):
        device = torch.device("cuda") if torch.cuda.is_available() else None
        plt.ion()

        for test in self.tests:
            for dataset in test.datasets:
                dataset.build(adc_bitwidth=self.adc_bitwidth, device=device)

                for network in test.networks:
                    assert network.inputs == dataset.cols

                    fig, axs = plt.subplots(2, figsize=(8,8))
                    axs[0].set_title("Loss")
                    axs[1].set_title("Accuracy")
    
                    if network.type == 'bitwise':
                        for i in range(self.adc_bitwidth-1, -1, -1):
                            self.run_eval_cnn(test, network, dataset, device, axs, bit=i)
                    else:
                        self.run_eval_cnn(test, network, dataset, device, axs, bit=-1)

                    run_hash = base36(hash(str(network) + str(dataset)))
                    fig.savefig(f'outputs/{run_hash}.png')
                    plt.close()


    def run_eval_cnn(self, test, network, dataset, device, axs, bit=-1):
        plot_period = 1000 if device else 10

        start_tm = time.monotonic()
        # if ? or self.overwrite
    
        dataset.builder.build_dataloaders(batch_size=test.batch_size, shuffle=True)
        dataloader  = dataset.builder.dataloader if bit == -1 else dataset.builder.dataloaders[bit]
        batch_count = -(len(dataset.builder.dataset) // -test.batch_size)
    
        cnn = network.create(dataset.len, dataset.cols)
        bit = "_" if bit == -1 else bit

        if bit == self.adc_bitwidth-1 or bit == -1: print(cnn)

        run_hash = base36(hash(str(network) + str(dataset))) + f"_{bit}"
        print(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test},{bit}")

        cnn = cnn.to(device)
    
        loss_arr = torch.empty(test.max_epochs, device=device)
        acc_arr  = torch.empty(test.max_epochs//plot_period, device=device)
        loss_g = None
        acc_g  = None

        criterion = nn.CrossEntropyLoss()
        optimizer = test.get_optimizer(cnn)
    
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

                if (epoch % plot_period) == 0:
                    _, predicted = torch.max(output, 1)
                    correct += (predicted == labels).sum()

            loss_arr[epoch] = loss

            if epoch % plot_period == 0:
                accuracy = correct / len(dataset.builder.dataset)
                acc_indx = epoch//plot_period
                acc_arr[acc_indx] = accuracy
                print(f'TRAINING: {run_hash}, Epoch {epoch:5}, Loss:     {loss.item()}')
                print(f'TRAINING: {run_hash}, Epoch {epoch:5}, Accuracy: {accuracy}')

                if loss_g: loss_g.remove()
                if acc_g:  acc_g.remove()
                loss_g = axs[0].plot(loss_arr.detach().cpu()[:epoch], color='gray', linestyle='dotted')[0]
                acc_g  = axs[1].plot(acc_arr.cpu()[:acc_indx+1],  color='gray', linestyle='dotted')[0]
                plt.pause(0.01)

            if accuracy >= test.max_accuracy:
                print("Reached target accuracy"); break

            if loss <= test.max_loss:
                print("Reached target loss"); break

        torch.save(cnn.state_dict(), f'outputs/{run_hash}.state')

        label = f'cnn[{bit}]'
        axs[0].plot(loss_arr.detach().cpu()[:epoch], label=label)
        axs[1].plot(acc_arr.cpu()[:epoch//plot_period+1], label=label)
        axs[0].legend()
        axs[1].legend()
        plt.pause(0.01)

        stop_tm = time.monotonic()
        runtime = stop_tm - start_tm

        with open(f'outputs/run_results.csv', 'a') as file:
            file.write(f"{run_hash},{network.name},{network},{dataset.name},{dataset},{test},{bit},{accuracy},{loss},{epoch},{runtime}\n")

# Main ###########################################

if __name__  == '__main__':
    regression = Regression('regression.json')
    regression.load()
    regression.run_all()

