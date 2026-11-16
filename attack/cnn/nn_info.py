#!/usr/bin/env python

###############################################################################
# File        : adc-side-channel/attack/cnn/nn_info.py
# Author      : kareemahmad
# Created     : 
# Description : Reports cnn information
###############################################################################

from classes import argparser, Regression

argparser.add_argument("-N", "--networks", type=str, nargs="+", help="Network to print information about")
argparser.add_argument("-D", "--datasets", type=str, nargs="+", help="Datasets to provide context for network")
argparser.add_argument(      "--nndebug",  action='store_true', help="Print information about cnn creation.")
args = argparser.parse_args()

regression = Regression(args)
regression.load()

def show_parameters(networks, datasets):
    for network in networks:
        for dataset in datasets:
            nn = network.create(dataset.len, dataset.cols, 5)
            print(f"{network.name} x {dataset.name} = {nn.num_params()}")

if args.networks and args.datasets:
    show_parameters(args.networks, args.datasets)

elif args.networks:
    show_parameters(args.networks, regression.datasets)

elif args.datasets:
    show_parameters(regression.networks, args.datasets)

else:
    for test in regression.tests:
        show_parameters(test.networks, test.datasets)


