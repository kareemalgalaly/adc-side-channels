import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import matplotlib.pyplot as plt
import pt_parser as parser
from torch.utils.data import DataLoader, TensorDataset

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
        self.fc1 = nn.Linear(5 * 2026, 100)
        self.fc2 = nn.Linear(100, 100)
        self.fc3 = nn.Linear(100, 100)
        # Output layer
        # 2 neurons, softmax
        self.o1 = nn.Linear(100, 2)

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
        x = x.view(x.size(0), -1)
        # Fully connected layers
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        # Output layer, softmax
        x = torch.softmax(self.o1(x), dim=1)
        return x

# get power traces
directory = os.path.dirname(os.path.abspath(__file__))
print(f"Getting power traces from {directory}...")
dataloaders = {}
datasets = parser.createPowerTraceDataSet(directory, 8).datasets
for i in range(8):
    # input size = 256, 20279, 1
    dataloaders[i] = DataLoader(datasets[i], batch_size=256, shuffle=True)
    print(f"Created dataloader for d{i}")

cnns = {}
# Create CNN per dataset
for i in range(8):
    # Model: our CNN
    # Loss function: not specified in paper, used Cross Entropy Loss
    # Optimizer: not specified in paper, used Adam
    cnns[i] = pt_CNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(cnns[i].parameters(), lr=0.001)
    # Train the model
    # Can use separate yml file
    for epoch in range(10):
        for powertraces, labels in dataloaders[i]:
            optimizer.zero_grad()
            output = cnns[i](powertraces)
            labels = labels.long()
            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()
            print(f'TRAINING: cnn[{i}], Epoch {epoch+1}, Loss: {loss.item()}')