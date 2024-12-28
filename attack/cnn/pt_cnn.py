import os
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import datetime

# import pt_parser as parser
import dataloader

# CNN defined in paper
class pt_CNN(nn.Module):
    def __init__(self, trace_len=3000):
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
        self.fc1 = nn.Linear(int(5 * (trace_len/10-2)), 100)
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
        x = torch.relu(self.fc3(x))
        # Output layer, softmax
        x = self.o2(self.o1(x))
        return x

pwd      = os.path.dirname(os.path.abspath(__file__))
proj_dir = os.path.dirname(os.path.dirname(pwd))
data_dir = os.path.join(proj_dir, 'analog', 'outfiles')
device   = torch.device("cuda") if torch.cuda.is_available() else None

mode = 'LINEAR'
plot_period = 1000 if device else 10
epoch_count = 10000
batch_size  = 256

if mode == 'LINEAR':
    dataset_dir = os.path.join(data_dir, 'sky_Dec_18_2151')
    trace_length    = 3000
    sample_mode     = None
    sample_interval = None
    sample_duration = None

elif mode == 'SAMPLED':
    dataset_dir = os.path.join(data_dir, 'sky')
    sample_mode = 'MIN'
    sample_interval = 0.1e-6
    sample_duration = 300e-6
    trace_length    = sample_duration / sample_interval

print(f"Launching on device {device}")

loader  = dataloader.TraceDatasetBuilder(adc_bitwidth=8, cache=True, device=device)
loader.add_files(dataset_dir, "sky_d(\\d+)_.*\\.txt", sample_mode=sample_mode, sample_int=sample_interval, sample_time=sample_duration)
loader.build()
#loader.cache_all()
loader.build_dataloaders(batch_size=batch_size, shuffle=True)

batch_count = -(len(loader.dataset) / -batch_size)

#for i in range(len(builder.dataset)):
#    print(builder.dataset.get_info(i))

#for dataset in builder.datasets:
#    print(dataset.bit_mask)
#    print(dataset[5][1])

#off = 0.0015
#ids = [0, 1, 2, 3, 4, 5, 6, 7, 40, 80, 160, 250]
#for i, label in enumerate(ids):
#    plt.plot(loader.dataset.get_by_label(label) + i*off, label=f'{label}')
#plt.gca().set_ylim([0.00, off*len(ids)])
#plt.legend()
#plt.show()

cnns = []
dataloaders = loader.dataloaders 
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
    cnn = pt_CNN(trace_length).to(device)
    cnns.append(cnn)
    loss_arr = torch.empty(epoch_count, device=device)
    acc_arr  = torch.empty(epoch_count, device=device)
    loss_g = None
    acc_g  = None

    criterion = nn.CrossEntropyLoss()
    #optimizer = optim.Adam(cnn.parameters(), lr=0.001)
    #optimizer = optim.Adam(cnn.parameters(), lr=0.0005) # linearized data
    optimizer = optim.Adam(cnn.parameters(), lr=0.0001) # sampled data

    # Train the model
    # Can use separate yml file
    for epoch in range(epoch_count):
        correct = 0
        for inputs, labels in dataloaders[i]:
            if device:
                inputs = inputs.cuda()
                labels = labels.cuda()

            # Do Training Step

            optimizer.zero_grad()
            output = cnn(inputs)

            loss = criterion(output, labels)
            loss.backward()
            optimizer.step()

            # Calculate Accuracy

            if (epoch % plot_period) == 0:
                _, predicted = torch.max(output, 1)
                correct += (predicted == labels).sum()
                accuracy = correct / 257

        acc_arr[epoch] = accuracy
        loss_arr[epoch] = loss

        if epoch % plot_period == 0:
            print(f'TRAINING: cnn[{i}], Epoch {epoch}, Loss: {loss.item()}')
            print(f'TRAINING: cnn[{i}], Epoch {epoch}, Accuracy: {accuracy}')
        #if epoch % 50 == 0: 
            if loss_g: loss_g.remove()
            if acc_g:  acc_g.remove()
            loss_g = axs[0].plot(loss_arr.detach().cpu(), color='gray', linestyle='dotted')[0]
            acc_g  = axs[1].plot(acc_arr.cpu(),  color='gray', linestyle='dotted')[0]
            plt.pause(0.01)

    torch.save(cnn.state_dict(), f'trained_models/{timestamp}_cnn_{i}.state')

    label = f'cnn[{i}]'
    axs[0].plot(loss_arr.detach().cpu(), label=label)
    axs[1].plot(acc_arr.cpu(),           label=label)
    axs[0].legend()
    axs[1].legend()
    plt.pause(0.01)

input("==== Job Complete. Press Enter to Exit ====")
