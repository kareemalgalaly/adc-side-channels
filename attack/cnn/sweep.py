#!/usr/bin/env python

###############################################################################
# File        : attack/cnn/sweep.py
# Author      : kareemahmad
# Created     : 
# Description : __main__ equivalent. Handles CNN training and testing
###############################################################################

import sys
sys.path
sys.path.append('../../script')

import os
import json
import subprocess
import numpy as np
import csvlib

import logging
logging.basicConfig(
    # filename = f"outputs/sweep.log",
    handlers = [
        logging.FileHandler('outputs/sweep.log'), #, mode='w'),
        logging.StreamHandler(sys.stdout)
        ],
    level    = logging.INFO,
    format   = "%(levelname)-6.5s %(message)s",
    datefmt  = "%Y-%m-%d %H:%M:%S"
    )
logger = logging.getLogger(__name__)

import argparse

argparser = argparse.ArgumentParser(prog="sweep")
argparser.add_argument("-r", "--repeat" , type=int, default=1, help="")
argparser.add_argument("-b", "--bit" ,    type=int, choices=range(8), default=None, help="")
argparser.add_argument("-s", "--seed" ,   type=int, default=1, help="")
args = argparser.parse_args()

ENV = dict(os.environ)
ENV["MKL_SERVICE_FORCE_INTEL"] = "1"

data = {
    "nlg_xp_tt" : {
        "path"        : "cmb_xp_tt",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 0
    },
    "dig_xp_tt" : {
        "path"        : "cmb_xp_tt",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 1
    },
    "cmb_xp_tt" : {
        "path"        : "cmb_xp_tt",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "columns"     : 2
    },
    "nlg_xp_ss" : {
        "path"        : "cmb_xp_ss",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 0
    },
    "dig_xp_ss" : {
        "path"        : "cmb_xp_ss",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 1
    },
    "cmb_xp_ss" : {
        "path"        : "cmb_xp_ss",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "columns"     : 2
    },
    "nlg_xp_fs" : {
        "path"        : "cmb_xp_fs",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 0
    },
    "dig_xp_fs" : {
        "path"        : "cmb_xp_fs",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "column"      : 1
    },
    "cmb_xp_fs" : {
        "path"        : "cmb_xp_fs",
        "format"      : "raw_s\\d+_(\\d+)\\.txt",
        "type"        : "raw",
        "len"         : 2560,
        "columns"     : 2
    }
}

defs = {
    "sample_mode"     : ["MAX"],
    "sample_interval" : 0.1e-6,
    "sample_duration" : 256e-6,
    "columns"         : 1,
    "normalizer"      : "zscore",
    "trace_scale"     : 1,
    "optimizer"       : "Adam",
    "loss"            : "CrossEntropyLoss",
    "loss_se"         : "MSELoss",
    "learning_rate"   : 0.0005,
    "learning_decay"  : 0,
    "max_learn_rate"  : 0.05,
    "max_epochs"      : 5000,
    "max_accuracy"    : 0.99,
    "max_loss"        : 0.0,
    "batch_size"      : -1,
    "train_split"     : 1
}
test_base = {
    "desc"          : "Automated",
    "learning_rate" : [0.0003],
    "learning_decay": 0.000025,
    "val_acc_cut"   : 0.2,
    "optimizer"     : "Amsgrad",
    "max_epochs"    : 5000
}

# Classes --------------------------------------------------

class CNN:
    names = {}
    index = 0

    def __init__(self, cnum=2, csiz=5, cchn=5, csdc=3/5, ccdc=1, fnum=3, fsiz=100, fdec=1, cpst="R:P(5,5)", fpst="R:BN1", mode='bw', **espec):
        self.spec = dict(
            cnum = cnum,
            csiz = csiz,
            cchn = cchn,
            csdc = csdc,
            ccdc = ccdc,
            fnum = fnum,
            fsiz = fsiz,
            fdec = fdec,
            cpst = cpst,
            fpst = fpst,
            mode = mode,
            **espec
            )
        key = frozenset(self.spec.items())
        cls = type(self)
        if key in self.names:
            self.name = cls.names[key]
        else:
            self.name = cls.names[key] = f"{cls.__name__.lower()}_{cls.index}"
            cls.index += 1

    def __str__(self):
        return self.name

    def __repr__(self):
        return "CNN(" + ", ".join(f'{k}={v!r}' for k, v in self.spec.items()) + ")"

    @classmethod
    def from_spec(cls, **spec):
        cnns = [cls(**spec)]
        
        for key, value in spec.items():
            if hasattr(value, "__iter__") and not isinstance(value, str):
                ncnns = []
                for v in value:
                    for c in cnns:
                        ncnns.append(c.modify({key : v}))
                cnns = ncnns

        return cnns

    def modify_spec(self, **spec):
        nspec = dict(self.spec)
        nspec.update(spec)
        return nspec

    def modify(self, spec):
        return type(self)(**self.modify_spec(**spec))

    def json(self):
        layers = []
        typ = None

        csiz = self.spec['csiz']
        csdc = self.spec['csdc']
        cchn = self.spec['cchn']
        ccdc = self.spec['ccdc']
        cpst = self.spec['cpst']

        for i in range(self.spec['cnum']):
            layers.append(f"C({cchn},{csiz},1)")
            if cpst: layers.append(cpst)
            csiz = max(int(csiz * csdc), 2)
            cchn = max(int(cchn * ccdc), 1)

        fsiz = self.spec['fsiz']
        fdec = self.spec['fdec']
        fpst = self.spec['fpst']

        for i in range(self.spec['fnum']):
            layers.append(f"F({fsiz})")
            if fpst: layers.append(fpst)
            fsiz = max(int(fsiz * fdec), 8)

        match self.spec['mode']:
            case 'bw':
                layers.append('F(2):S')
                typ = "bitwise"
            case 'se':
                layers.append('F(1)')
                typ = "single_ended"
            case 'mb': 
                layers.append('F(8)')
                typ = "multibit"
            case _: 
                raise NotImplementedError

        return dict(definition=':'.join(layers), type=typ)

class PCNN(CNN):
    names = {}
    index = 0

    def __init__(self, pcnn=None, awgt=None, dwgt=None, pcrp=6, **spec):
        super().__init__(pcnn=pcnn, awgt=awgt, dwgt=dwgt, pcrp=pcrp, **spec)

    def json(self):
        jdct = super().json()
        pcnn = self.spec["pcnn"]
        awgt = self.spec["awgt"]
        dwgt = self.spec["dwgt"]
        pcrp = self.spec["pcrp"]
        jdct["definition"] = f"T({pcnn},{awgt},{pcrp},{pcnn},{dwgt},{pcrp}):{jdct["definition"]}"
        return jdct

def gen_tests(cnns, typ, norm):
    if isinstance(norm, list):
        tests = []
        for n in norm:
            tests.extend(gen_tests(cnns, typ, n))
        return tests

    match typ:
        case "combined":
            test = dict(test_base)
            test['networks'] = [cnn.name for cnn in cnns]
            test['datasets'] = [f"cmb_xp_tt{norm}"]
            test['test_dataset'] = [f"cmb_xp_ss{norm}"] #, "cmb_xp_fs"]
            return [test]

        case "analog":
            atest = dict(test_base)
            atest['networks'] = [cnn.name for cnn in cnns]
            atest['datasets'] = [f"nlg_xp_tt{norm}"]
            atest['test_dataset'] = [f"nlg_xp_ss{norm}"] #, "cmb_xp_fs"]
            return [atest]

        case "digital":
            dtest = dict(atest)
            dtest['datasets'] = [f"dig_xp_tt{norm}"]
            dtest['test_dataset'] = [f"dig_xp_ss{norm}"] #, "cmb_xp_fs"]
            return [dtest]

        case "single":
            atest = dict(test_base)
            atest['networks'] = [cnn.name for cnn in cnns]
            atest['datasets'] = [f"nlg_xp_tt{norm}"]
            atest['test_dataset'] = [f"nlg_xp_ss{norm}"] #, "cmb_xp_fs"]
            dtest = dict(atest)
            dtest['datasets'] = [f"dig_xp_tt{norm}"]
            dtest['test_dataset'] = [f"dig_xp_ss{norm}"] #, "cmb_xp_fs"]
            return [atest, dtest]

        case "singlept":
            atest = dict(test_base)
            atest['networks'] = [cnn.name for cnn in cnns]
            atest['datasets'] = [f"nlg_xp_tt{norm}"]
            atest['test_dataset'] = [f"nlg_xp_ss{norm}"] #, "cmb_xp_fs"]
            atest['train_split'] = 0.4
            dtest = dict(atest)
            dtest['datasets'] = [f"dig_xp_tt{norm}"]
            dtest['test_dataset'] = [f"dig_xp_ss{norm}"] #, "cmb_xp_fs"]
            dtest['train_split'] = 0.4
            return [atest, dtest]

        case "pretrained":
            tests = gen_tests([cnns[0]], "singlept", norm)
            tests += gen_tests(cnns[1:], "combined", norm)
            return tests

    raise NotImplementedError(f"Unrecognized type {typ}")

def load_sweep_csv(cnnd={}, ctgs=[]):
    csv = csvlib.read("outputs/sweep.csv")
    csv.add_computed_column(lambda a,p: (p-a) > 0.2, "Accuracy", "Peak Accuracy", name="Crashed")
    csv.add_computed_column(lambda p,b: p > (0.4 if b == "_" else 0.8), "Peak Accuracy", "Bit", name="Learning")
    for ctg in ctgs: 
        csv.add_computed_column(lambda n: cnnd[n].spec.get(ctg, None), "Network", name=ctg)
    return csv

def get_ctgs(spec):
    return [k for k, v in spec.items() if hasattr(v, "__iter__") and not isinstance(v, str)]

def get_best_cnn(table, cnnd, pretrained=False):
    maxacc = 0
    maxcnn = None
    maxnrm = None

    res = []
    for tests, data in table.items():
        nrm = tests[0][-2]
        cnn = tests[0][-1]
        acc = data[0]
        if pretrained and cnn.startswith("c"): continue
        res.append(f"{cnn} {acc}")
        if acc > maxacc:
            maxacc = acc
            maxcnn = cnn
            maxnrm = nrm

    logger.info("Results:\n  %s", "\n  ".join(res))

    cnn = cnnd[maxcnn]
    cnn.nrm = maxnrm

    return cnn

def evaluate_core(data, defs, rpt, bit, typ, cnns, norm=[""], preview=False, overwrite=True):
    jdct = dict(
        networks = {cnn.name:cnn.json() for cnn in cnns},
        datasets = data,
        tests = gen_tests(cnns, typ, norm),
        defaults = defs
    )

    with open("experiments/sweep.json", "w") as file:
        json.dump(jdct, file, indent=2)

    program = ["./regress.py", "-f", "-r", str(rpt), "--json", "experiments/sweep.json", 
               "--headless", "--csv", "sweep", "--seed", str(seed)]

    if bit is not None: program.extend(["--bit", str(bit)])
    if overwrite: program.append("--overwrite")
    if preview:
        program.append("--preview")
        r = subprocess.run(program, env=ENV, capture_output=True, text=True)
        return r.stdout

    r = subprocess.run(program, env=ENV)
    assert r.returncode == 0

    with open("outputs/sweep_all.csv", "a") as wfile:
        with open ("outputs/sweep.csv", "r") as rfile:
            rfile.readline()
            wfile.write(rfile.read())

def evaluate(data, defs, rpt, bit, typ, norm=[""], **spec):
    cnns = CNN.from_spec(**spec)
    logger.info("Evaluate:\n  spec = %s\n  %s", str(spec), "\n  ".join(f"{cnn} {cnn!r}" for cnn in cnns))
    cnnd = {cnn.name : cnn for cnn in cnns}
    ctgs = get_ctgs(spec)

    evaluate_core(data, defs, rpt, bit, typ, cnns, norm=norm)
    csv = load_sweep_csv(cnnd, ctgs)

    cdata = {
        "Test Accuracy" : np.average
        }
    filters = {
        "Crashed": lambda x: not x,
        "Learning": lambda x: x,
        }
    if bit is not None: filters["Bit"] = lambda x: x == bit
    cols = ["Bit"]
    rows = ["Test Dataset", *ctgs, "Network"]
    if norm and norm[0] != "":
        csv.add_computed_column(lambda n: n[n.find(":")+1:n.find(";")], "Normalizer", name="Normtype")
        rows.insert(-1, "Normtype")

    table = csv.pivot(data=cdata, filters=filters, cols=cols, rows=rows)
    csv.write_pivot("outputs/sweep_pivots.csv", data=cdata, filters=filters, cols=cols, rows=rows, pivot=table, mode="a")
    cnn = get_best_cnn(table, cnnd)

    logger.info(f"Best CNN = {cnn} {cnn!r}")
    return cnn

def evaluate_pretrain(cnn, data, defs, rpt, bit, **spec):
    out = evaluate_core(data, defs, rpt, bit, "singlept", [cnn], preview=True)
    out = out.split("\n")
    awgt = None
    dwgt = None
    for line in out:
        if   "nlg" in line: awgt = line[:line.find(",")]
        elif "dig" in line: dwgt = line[:line.find(",")]
    spec['awgt'] = awgt
    spec['dwgt'] = dwgt
    spec['pcnn'] = cnn.name

    # tests = gen_tests([cnn], "single")
    cnns = [cnn] + PCNN.from_spec(**spec)
    logger.info("Evaluate:\n  pretraining {%s}\n  spec = %s\n  %s", str(cnn.spec), str(spec), "\n  ".join(f"{cnn} {cnn!r}" for cnn in cnns))
    cnnd = {cnn.name : cnn for cnn in cnns}
    ctgs = get_ctgs(spec)

    evaluate_core(data, defs, rpt, bit, "pretrained", cnns)
    csv = load_sweep_csv(cnnd, ctgs)
    
    cdata = {
        "Test Accuracy" : np.average
        }
    filters = {
        "Crashed": lambda x: not x,
        "Learning": lambda x: x,
        # "Network": lambda x: x != cnn.name,
        }
    if bit is not None: filters["Bit"] = lambda x: x == bit
    cols = ["Bit"]
    rows = ["Test Dataset", *ctgs, "Network"]

    table = csv.pivot(data=cdata, filters=filters, cols=cols, rows=rows)
    csv.write_pivot("outputs/sweep_pivots.csv", data=cdata, filters=filters, cols=cols, rows=rows, pivot=table, mode="a")
    cnn = get_best_cnn(table, cnnd, pretrained=True)

    logger.info(f"Best CNN = {cnn} {cnn!r}")
    return cnn

# Sweeps ---------------------------------------------------

def simple_sweep(mode):
    logger.info("Simple sweep: %s", mode)

    if mode == "combined":
        best = CNN(cnum = 2, cchn = 10, csiz = 5, fnum = 3, fsiz = 100)
    else:                              
        best = CNN(cnum = 2, cchn = 5, csiz = 5, fnum = 3, fsiz = 100)

    spec = best.modify_spec(cpst=("R:P(5,5)","R:P(5,5):BN1"), fpst=("R:BN1","R"), csdc=(1,0.6))
    best = evaluate(data, defs, rpt, bit, mode, **spec)

    spec = best.modify_spec(csiz=(5, 10, 20, 40), cchn=(5, 10, 20, 30))
    best = evaluate(data, defs, rpt, bit, mode, **spec)

    spec = best.modify_spec(cnum = (0,1,2,3,4), fnum = (1,2,3,4))
    best = evaluate(data, defs, rpt, bit, mode, **spec)

    spec = best.modify_spec(fdec = (0.5,1), fsiz = (50,100,200))
    best = evaluate(data, defs, rpt, bit, mode, **spec)

    # spec = best.modify_spec(ccdc=(1,0.5), csdc=(1,0.6), fdec=(1,0.5))
    # best = evaluate(data, defs, rpt, bit, mode, **spec)

    return best

def pretrained_sweep(sngl):
    logger.info("Pretrained sweep")

    base = PCNN(cnum=0)

    # pretrain
    lmin = sngl.spec['cnum'] * 3
    lmax = sngl.spec['fnum'] * 3 + lmin
    spec = base.modify_spec(pcrp = range(max(lmin,3), lmax+1, 3), fnum = (1, 2, 3, 4, 5))
    best = evaluate_pretrain(sngl, data, defs, rpt, bit, **spec)

    spec = best.modify_spec(fdec=(0.5,1), fsiz=(50,100,200))
    best = evaluate_pretrain(sngl, data, defs, rpt, bit, **spec)

    spec = best.modify_spec(fpst=("R:BN1","R"))
    best = evaluate_pretrain(sngl, data, defs, rpt, bit, **spec)

    # spec = best.modify_spec(pcrp = (6, 9, 12, 15), cnum = (0, 1))
    # best = evaluate_pretrain(sngl, data, defs, rpt, bit, **spec)

    return best

def normalizer_sweep(mode):
    logger.info("Normalizer sweep: %s", mode)
    normalizers = ["autoscale", "zscore", "robust", "tautoscale", "tzscore", "trobust", "raw"]

    dsnames = list(data.keys())
    for norm in normalizers:
        for dsname in dsnames:
            dsinfo = dict(data[dsname])
            dsinfo['normalizer'] = norm
            data[f"{dsname}{norm}"] = dsinfo

    if mode == "combined":
        best = CNN(cnum = 2, cchn = 10, csiz = 5, fnum = 3, fsiz = 100, fpst="R")
    else:                              
        best = CNN(cnum = 2, cchn = 5, csiz = 5, fnum = 3, fsiz = 100, fpst="R")

    best = evaluate(data, defs, rpt, bit, mode, norm=normalizers, **best.spec)

    logger.info("Selected Normalizer: %s", best.nrm)
    defs['normalizer'] = best.nrm
    return best.nrm

# Main -----------------------------------------------------

if __name__ == "__main__":
    bit = args.bit
    rpt = args.repeat
    seed = args.seed

    # # Test Eval
    # best = evaluate(cnns, data, defs, test_base, num_rpt, bit_sel, csiz=(5, 10), cchn=(5, 10))
    # exit(1)

    logger.info(f"Starting Evaluation\n  repeat = {rpt}\n  bit = {bit}")

    # 5 min
    normalizer_sweep("analog")
    best = simple_sweep("analog")

    # # 7 min
    pretrained_sweep(best)
    pretrained_sweep(CNN(cnum = 2, cchn = 5, csiz = 5, fnum = 3, fsiz = 100))

    # 13 min
    normalizer_sweep("combined")
    simple_sweep("combined")

