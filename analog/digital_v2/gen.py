import os
import argparse
import random

argparser = argparse.ArgumentParser(prog="gen")
argparser.add_argument("-i", "--interactive", action="store_true", help="interactive mode")
argparser.add_argument("-p", "--pixels",  type=int, default=5, help="Number of pixels")
argparser.add_argument("-s", "--seed",    type=int, default=0, help="Initial seed")
argparser.add_argument("-n", "--numsim",  type=int, default=1, help="Number of simulations")
argparser.add_argument("-c", "--corner",  type=str, default="tt", help="Corner to simulate")
argparser.add_argument("-v", "--version", type=str, default="v3", help="Version of sampler")
args = argparser.parse_args()

jobs = ["#!/bin/bash"]

for s in range(args.seed, args.seed+args.numsim):
    random.seed(s)

    dvals = [str(random.randint(0, 255)) for p in range(args.pixels)]
    dcmd  = "dvals=eval:[" + ",".join(dvals) + "]"
    dnam  = "_".join(dvals)

    rnam = f"outfiles/{args.version}_{args.corner}_{args.pixels}/rawfile_s{s}_{dnam}"
    tnam = f"outfiles/{args.version}_{args.corner}_{args.pixels}/trace_s{s}_{dnam}"

    job_sim = f"ngspice -b -r {rnam} <(python3 ../../script/teng.py -g template_batch.cir pixels=eval:{args.pixels} corner={args.corner} version={args.version} {dcmd})"
    job_prs = f"ngspice <(python3 ../../script/teng.py template_batch_post.cir rawfile={rnam} outfile={tnam})"

    jobs.append(f"{job_sim};{job_prs}")

for j in jobs: print(j)

