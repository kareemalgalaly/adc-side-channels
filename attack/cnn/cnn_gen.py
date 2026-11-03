###############################################################################
# File        : attack/cnn/cnn_gen.py
# Author      : kareemahmad
# Created     : 
# Description : Defines a generic CNN constructor based on string definitions
#
# Format: colon separated string where entries are of the following
#   F(out_nodes)                               : Fully Connected
#   C(out_channels, kernel, stride, [groups])  : Convolutional
#   BN1                                        : Batch Norm
#   P(kernel, stride)                          : Pooling
#   R                                          : ReLU
#   S                                          : Softmax
###############################################################################


import re
import torch
import torch.nn as nn
import traceback
from operator import mul

## Regex Definitions ---------------------------------------

re_f  = re.compile('F\\((\\d+)\\)')
re_c  = re.compile('C\\((\\d+),(\\d+),(\\d+)(,\\d+)?\\)')
# re_c2 = re.compile('C\\((\\d+),(\\d+),(\\d+),(\\d+),(\\d+)\\)') # ch_out, size_x, size_y, stride_x, stride_y 
re_b  = re.compile('BN([12])')
# re_b  = re.compile('BN([12])(\(\d+\))?')
re_p  = re.compile('P\\((\\d+),(\\d+)\\)')
# re_p2 = re.compile('P\\((\\d+),(\\d+),(\\d+),(\\d+)\\)')
re_t  = re.compile('T\\(([^)]+)\\)')

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


def build_cnn(definition, networks, bit=-1, debug=False):
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
            try:
                w_in, c_in = shapes[-1]
            except:
                w_in, h_in, c_in = shapes[-1]
                assert h_in == 1
            kernel = int(gs[1])
            stride = int(gs[2])
            groups = int(gs[3][1:]) if gs[3] else 1
            out_shape = get_output_size(w_in, c_in, c_out, kernel=kernel, stride=stride)

            layers.append(nn.Conv1d(in_channels=c_in, out_channels=c_out, kernel_size=kernel, stride=stride, groups=groups))
            shapes.append(out_shape)

        # elif m := re_c2.match(token):
        #     gs    = m.groups()
        #     c_out = int(gs[0])
        #     print(shapes)
        #     try:
        #         w_in, h_in, c_in = shapes[-1]
        #     except:
        #         w_in, h_in = shapes[-1]
        #         c_in = 1
        #     kernel = (int(gs[1]), int(gs[2]))
        #     stride = (int(gs[3]), int(gs[4]))
        #     out_shape = (get_output_size(w_in, c_in, c_out, kernel=kernel[0], stride=stride[0])[0],
        #                 *get_output_size(h_in, c_in, c_out, kernel=kernel[1], stride=stride[1]))

        #     layers.append(nn.Conv2d(in_channels=c_in, out_channels=c_out, kernel_size=kernel, stride=stride))
        #     shapes.append(out_shape)

        elif m := re_b.match(token):
            gs = m.groups()
            dim = int(gs[0])
            cin = shapes[-1][-1]
            shapes.append(shapes[-1])
            # print(f"BatchNorm1({cin}) <- {shapes}")
            match dim:
                case 1 : layers.append(nn.BatchNorm1d(cin))
                # case 2 : layers.append(nn.BatchNorm2d(cin))
                case _ : raise RuntimeError("Unsupported dimensionality")

        elif m := re_p.match(token):
            gs = m.groups()
            try:
                w_in, c_in = shapes[-1]
            except:
                w_in, h_in, c_in = shapes[-1]
                assert h_in == 1
            kernel = int(gs[0])
            stride = int(gs[1])
            out_shape = get_output_size(w_in, c_in, kernel=kernel, stride=stride)

            layers.append(nn.MaxPool1d(kernel_size=kernel, stride=stride))
            shapes.append(out_shape)

        # elif m := re_p2.match(token):
        #     gs = m.groups()
        #     w_in, h_in, c_in = shapes[-1]
        #     kernel = (int(gs[0]), int(gs[1])) 
        #     stride = (int(gs[2]), int(gs[3]))
        #     out_shape = (get_output_size(w_in, c_in, c_out, kernel=kernel[0], stride=stride[0])[0],
        #                 *get_output_size(h_in, c_in, c_out, kernel=kernel[1], stride=stride[1]))

        #     layers.append(nn.MaxPool2d(kernel_size=kernel, stride=stride))
        #     shapes.append(out_shape)

        elif m := re_t.match(token):
            info = m.group(1).split(',')
            num_layer = len(info) // 3
            input_len = shapes[-1][0] 
            layer_chs = shapes[-1][1] // num_layer

            ns = []
            ls = []
            cs = []

            for i in range(0, len(info), 3):
                ntw = networks[info[i]]
                if bit == -1:
                    wgt = f"outputs/{info[i+1]}.state"
                else:
                    wgt = f"outputs/{info[i+1]}_{bit}.state"
                stp = int(info[i+2])
                dfn = f"{input_len},{layer_chs}:{ntw.definition}"
                lyr = GenericCNN(dfn, networks, cols=layer_chs, stop=stp, bit=bit, debug=False)
                lyr.load_state_dict(torch.load(wgt, map_location='cpu', weights_only=True)) # moved to gpu later
                ls.append(lyr.shapes[stp][0])
                cs.append(1 if len(lyr.shapes[stp]) == 1 else lyr.shapes[stp][1])
                ns.append(lyr)

            output_len = ls[0]
            output_chs = sum(cs)
            for l in ls: assert l == output_len

            shape = (output_len, output_chs)

            layers.append(StackCNN(ns))
            shapes.append(shape)

        elif token == 'R':
            layers.append(nn.ReLU())
            shapes.append(shapes[-1])

        elif token == 'S':
            layers.append(nn.Softmax(dim=1))
            shapes.append(shapes[-1])

        else:
            raise RuntimeError(f"Could not parse definition entry <{token}>")

    if debug:
        print(shapes)
        print(*layers, sep="\n")
    return nn.ModuleList(layers), flatten, shapes

## Pytorch class -------------------------------------------

class GenericCNN(nn.Module):
    def __init__(self, definition, networks, cols=1, bit=-1, debug=False, stop=None):
        super(GenericCNN, self).__init__()
        self.layers, self.flatten, self.shapes = build_cnn(definition, networks, bit=bit, debug=debug)
        self.debug = debug
        self.cols  = cols

        if stop is None: 
            self.stop = len(self.layers)
        else:
            self.stop  = stop if stop > 0 else len(self.layers) + stop - 1

    def forward(self, x):
        if self.cols == 1:
            x = x.unsqueeze(1) 

        for i, layer in zip(range(self.stop), self.layers):
            if i == self.flatten:
                x = x.view(x.size(0), -1)
            try:
                x = layer(x)
            except Exception as e:
                print(f"\nError on layer {i} {layer}\n{traceback.format_exc()}")
                print(i, x.shape, layer)
                exit(1)
        return x


class StackCNN(nn.Module):
    def __init__(self, layers):
        super(StackCNN, self).__init__()
        self.layers = nn.ModuleList(layers)

    def forward(self, x):
        outputs = []

        # with torch.no_grad(): # TODO this gives worse results and is not typically used when pretraining as far as I know
        for i, layer in enumerate(self.layers):
            inp = x[:, i, :]
            outputs.append(layer(inp))

        return torch.cat(outputs, dim=1)
    
## Demo example --------------------------------------------

if __name__ == "__main__":
    print(build_cnn("3000,1:C(5,5,1):R:P(5,5):C(5,3,1):R:P(2,2):F(100):R:F(100):R:F(100):R:F(2):S"))

