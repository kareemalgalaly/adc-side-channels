import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, TensorDataset
import datetime

# import pt_parser as parser
import dataloader

# CNN defined in paper
class pt_CNN(nn.Module):
    def __init__(self):
        super(pt_CNN, self).__init__()
        # 1-D convolution layers
        # Activation = ReLU
        # 5 filters, kernel size = 5, stride = 1
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=5, kernel_size=5, stride=1)
        self.conv2 = nn.Conv1d(in_channels=5, out_channels=5, kernel_size=3, stride=1)
        # Pooling layers
        # MaxPool, pooling size = 5, stride = 5
        self.pool1 = nn.MaxPool1d(kernel_size=5, stride=5)
        self.pool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        # Fully connected layers
        # Activation = ReLU
        # 100 neurons
        self.fc1 = nn.Linear(5 * 298, 100)
        self.fc2 = nn.Linear(100, 100)
        self.fc3 = nn.Linear(100, 100)
        # Output layer
        # 2 neurons, softmax
        self.o1 = nn.Linear(100, 2)
        self.o2 = nn.Softmax(dim=1)

    def forward(self, x):
        x = x.unsqueeze(1)
        # First convolutional layer
        x = torch.relu(self.conv1(x))
        # First maxpool
        x = self.pool1(x)
        # Second convolutional layer
        x = torch.relu(self.conv2(x))
        # Second maxpool
        x = self.pool2(x)
        # Flatten the output
        # 3000 -> 5 * 298
        x = x.view(x.size(0), -1)
        # Fully connected layers
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        #x = torch.relu(self.fc3(x))
        # Output layer, softmax
        x = self.o2(self.o1(x))
        return x

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')

builder  = dataloader.TraceDatasetBuilder(adc_bitwidth=8, cache=True)
builder.add_files(os.path.join(data_dir, 'sky_Dec_18_2151'), "sky_d(\\d+)_.*\\.txt", 0)
builder.build()
builder.build_dataloaders(batch_size=256, shuffle=True)

#for i in range(len(builder.dataset)):
#    print(builder.dataset.get_info(i))

#for dataset in builder.datasets:
#    print(dataset.bit_mask)
#    print(dataset[5][1])

cnns = []
dataloaders = builder.dataloaders 
timestamp   = datetime.datetime.now().strftime('%Y%m%d_%H%M')

plt.ion()
figs, axs = plt.subplots(2)
axs[0].set_title("Loss")
axs[1].set_title("Accuracy")

# Create CNN per dataset
for i in range(7,-1,-1):
    # Model: our CNN
    # Loss function: not specified in paper, used Cross Entropy Loss
    # Optimizer: not specified in paper, used Adam
    cnn = pt_CNN()
    cnns.append(cnn)
    loss_arr = []
    acc_arr  = []
    loss_g = None
    acc_g  = None

    criterion = nn.CrossEntropyLoss()
    #optimizer = optim.Adam(cnn.parameters(), lr=0.001)
    optimizer = optim.Adam(cnn.parameters(), lr=0.0005)

    # Train the model
    # Can use separate yml file
    for epoch in range(2000):
        correct = 0
        for powertraces, labels in dataloaders[i]:
            optimizer.zero_grad()
            output = cnn(powertraces)
            labels = labels.long()

            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(output, 1)
            correct += (predicted == labels).sum()
        accuracy = correct / 257
        acc_arr.append(accuracy)
        loss_arr.append(loss.item())
        if epoch % 10 == 0:
            print(f'TRAINING: cnn[{i}], Epoch {epoch+1}, Loss: {loss.item()}')
            print(f'TRAINING: cnn[{i}], Epoch {epoch+1}, Accuracy: {accuracy}')
        if epoch % 50 == 0: 
            if loss_g: loss_g.remove()
            if acc_g:  acc_g.remove()
            loss_g = axs[0].plot(loss_arr, color='lightgray', linestyle='dotted')[0]
            loss_a = axs[1].plot(acc_arr,  color='lightgray', linestyle='dotted')[0]
            plt.pause(0.01)

    torch.save(cnn.state_dict(), f'trained_models/{timestamp}_cnn_{i}.state')

    label = f'cnn[{i}]'
    axs[0].plot(loss_arr, label=label)
    axs[1].plot(acc_arr,  label=label)
    axs[0].legend()
    axs[1].legend()
    plt.pause(0.01)

plt.pause(60*10)
