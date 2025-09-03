###############################################################################
# File        : attack/cnn/cnn_gen.py
# Author      : kareemahmad
# Created     : 
# Description : Defines a generic CNN constructor based on string definitions
#
# Format: colon separated string where entries are of the following
#   F(out_nodes)                     : Fully Connected
#   C(out_channels, kernel, stride)  : Convolutional
#   P(kernel, stride)                : Pooling
#   R                                : ReLU
#   S                                : Softmax
###############################################################################


import torch.nn as nn
import re
from operator import mul

## Regex Definitions ---------------------------------------

re_f = re.compile('F\\((\\d+)\\)')
re_c = re.compile('C\\((\\d+),(\\d+),(\\d+)\\)')
re_p = re.compile('P\\((\\d+),(\\d+)\\)')

## Helper Functions ----------------------------------------

def get_output_size(w_in, c_in, c_out=None, kernel=3, padding=0, dilation=1, stride=1):
    """
    Helper function to determine output shape after convolution or pool layer.
    From https://www.loganthomas.dev/blog/2024/06/12/pytorch-layer-output-dims.html
    """
    c_out = c_in if c_out is None else c_out
    w_out = ((w_in + 2 * padding - dilation * (kernel - 1) - 1) // stride) + 1
    return w_out, c_out

def flatten_shape(shape):
    ret = shape[0]
    for i in shape[1:]: ret *= i
    return ret

def build_cnn(definition, debug=False):
    tokens = definition.replace(" ", "").split(":")
    in_shp = tuple(int(s) for s in tokens[0].split(','))
    shapes = [in_shp]
    layers = []
    flatten = -1

    for token in tokens[1:]:
        if m := re_f.match(token):
            out_shape = int(m.groups()[0])

            if flatten == -1: flatten = len(layers)

            layers.append(nn.Linear(flatten_shape(shapes[-1]), out_shape))
            shapes.append((out_shape,))


        elif m := re_c.match(token):
            gs    = m.groups()
            c_out = int(gs[0])
            w_in, c_in = shapes[-1]
            kernel = int(gs[1])
            stride = int(gs[2])
            out_shape = get_output_size(w_in, c_in, c_out, kernel=kernel, stride=stride)

            layers.append(nn.Conv1d(in_channels=c_in, out_channels=c_out, kernel_size=kernel, stride=stride))
            shapes.append(out_shape)

        elif m := re_p.match(token):
            gs = m.groups()
            w_in, c_in = shapes[-1]
            kernel = int(gs[0])
            stride = int(gs[1])
            out_shape = get_output_size(w_in, c_in, kernel=kernel, stride=stride)

            layers.append(nn.MaxPool1d(kernel_size=kernel, stride=stride))
            shapes.append(out_shape)

        elif token == 'R':
            layers.append(nn.ReLU())

        elif token == 'S':
            layers.append(nn.Softmax(dim=1))

        else:
            raise RuntimeError(f"Could not parse definition entry <{token}>")

    if debug: print(shapes)
    return nn.ModuleList(layers), flatten

## Pytorch class -------------------------------------------

class GenericCNN(nn.Module):
    def __init__(self, definition, debug=False):
        super(GenericCNN, self).__init__()
        self.layers, self.flatten = build_cnn(definition, debug)
        self.debug = debug

    def forward(self, x):
        #if self.debug: print(x.shape, "input")
        x = x.unsqueeze(1)
        #if self.debug: print(x.shape, "unsqueeze")
        for i, layer in enumerate(self.layers):
            if i == self.flatten:
                x = x.view(x.size(0), -1)
                #if self.debug: print(x.shape, "flatten")
            x = layer(x)
            #if self.debug: print(x.shape, layer)
        return x
    
## Demo example --------------------------------------------

if __name__ == "__main__":
    print(build_cnn("3000,1:C(5,5,1):R:P(5,5):C(5,3,1):R:P(2,2):F(100):R:F(100):R:F(100):R:F(2):S"))

