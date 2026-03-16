###############################################################################
# File        : attack/cnn/normalizer.py
# Author      : kareem
# Created     : 2025 Nov 06
# Description : Normalizing structure (and also trace cache)
###############################################################################

import numpy as np
from sklearn.preprocessing import RobustScaler
from utils import ProgressBar

## Generic Constructor -------------------------------------

def build_normalizer(cache, nparams):
    match nparams['norm']:
        case None       : return NOPNormalizer(cache, nparams)
        case "scale"    : return ScaleNormalizer(cache, nparams)
        case "autoscale": return AutoscaleNormalizer(cache, nparams)
        case "zscore"   : return ZScoreNormalizer(cache, nparams)
        case "robust"   : return RobustNormalizer(cache, nparams)
        case _          : raise NotImplementedError(f"Unknown normalization technique {nparams['norm']}")

## Normalizers ---------------------------------------------

# ------------------------------------------------
# class: Normalizer
# - Base normalizer class, do not instantiate
# ------------------------------------------------

class Normalizer:
    def __init__(self, cache, params):
        self.cols = cache.cols
        self.cache = cache
        self.trained = False
        self.params = params

    def train(self):
        raise NotImplementedError

    def load_training(self, them):
        assert(type(them) == type(self))
        self.params = them.params
        self.trained = True

    def fit(self, index):
        if not self.trained: 
            self.train()
            self.trained = True

        trace = self.cache.nrm_cache[index] = self.do_fit(index)
        return trace

    def do_fit(self, index):
        raise NotImplementedError

# ------------------------------------------------
# class: NOPNormalizer
# - A normalizer that does nothing
# ------------------------------------------------

class NOPNormalizer(Normalizer):
    def train(self): return
    def do_fit(self, index): return self.cache.raw_cache[index].trace

# ------------------------------------------------
# class: ScaleNormalizer
# - A normalizer that uniformly scales all traces
# ------------------------------------------------

class ScaleNormalizer(Normalizer):
    def __init__(self, cache, params):
        super().__init__(cache, params)
        self.mult = params["mult"]

    def train(self): return

    def load_training(self, them):
        super().load_training(them)
        self.mult = them.mult

    def do_fit(self, index): return self.cache.raw_cache[index].trace * self.mult

# ------------------------------------------------
# class: AutoscaleNormalizer
# - A normalizer that uniformly scales all traces
# - to achieve average value of params[mult]
# ------------------------------------------------

class AutoscaleNormalizer(ScaleNormalizer):
    def __init__(self, cache, params):
        super().__init__(cache, params)
        self.average = params["mult"]
        self.mult = None

    def train(self):
        progress = ProgressBar(f_start=f"{{state}} {self.cache.name} ", max_val=len(self.cache))
        progress.start(state="Loading Dataset")

        ctot = 0
        for i, tinf in enumerate(self.cache.iter_raw()):
            ctot += np.sum(tinf.trace)
            progress.update(i)
        tnum = float((i+1) * np.prod(tinf.trace.shape))

        average = ctot / tnum
        self.mult = self.average / average
        progress.stop(i+1)

# ------------------------------------------------
# class: AutoscaleNormalizer
# - A normalizer that uniformly shifts and scales 
# - all traces to achieve average value 0 and 
#   stddev of 1
# ------------------------------------------------

class ZScoreNormalizer(Normalizer):
    def __init__(self, cache, params):
        super().__init__(cache, params)
        self.avg = None
        self.std = None
        self.off = params["mult"]

    def train(self):
        progress = ProgressBar(f_start=f"{{state}} {self.cache.name} ", max_val=len(self.cache))
        progress.start(state="Loading Dataset")

        all_data = []
        for i, tinf in enumerate(self.cache.iter_raw()):
            all_data.append(tinf.trace)
            progress.update(i)

        all_data = np.array(all_data)
        self.avg = np.mean(all_data)
        self.std = np.std(all_data, mean=self.avg)
        print("avg", self.avg)
        print("std", self.std)
        progress.stop(i+1)

    def load_training(self, them):
        super().load_training(them)
        self.avg = them.avg
        self.std = them.std

    def do_fit(self, index): return (self.cache.raw_cache[index].trace - self.avg) / self.std + self.off

# ------------------------------------------------
# class: RobustNormalizer
# - A normalizer that uses scikit's RobustScaler
#   to per-channel normalize traces in a dataset 
# ------------------------------------------------

class RobustNormalizer(Normalizer):
    def __init__(self, cache, params):
        super().__init__(cache, params)
        self.fitted = False

    def train(self):
        progress = ProgressBar(f_start=f"{{state}} {self.cache.name} ", max_val=len(self.cache))
        progress.start(state="Loading Dataset")

        traces = []
        for i, tinf in enumerate(self.cache.iter_raw()):
            traces.append(tinf.trace)
            progress.update(i)
        traces = np.array(traces)

        progress.update(i, state="Fitting Dataset")

        if self.cols == 1:
            scaler = RobustScaler(quantile_range=(10, 90))
            scaler.fit(traces)
            self.scalers = [scaler]
            # print(scaler.center_, scaler.scale_)

        else:
            fchanls = []
            self.scalers = []
            for c in range(self.cols):
                scaler = RobustScaler(quantile_range=(10, 90))
                scaler.fit(traces[:, c])
                fchanls.append(scaler.transform(traces[:, c]))
                # print(scaler.center_, scaler.scale_)
                self.scalers.append(scaler)
            ftraces = np.stack(fchanls, axis=1)
            self.cache.nrm_cache = ftraces
        
        self.trained = True
        self.fit_all()
        progress.stop(i+1)

    def load_training(self, them):
        super().load_training(them)
        self.scalers = them.scalers
        self.trained = True
        self.fitted = False

    def fit_all(self):
        progress = ProgressBar(f_start=f"{{state}} {self.cache.name} ", max_val=len(self.cache))
        progress.start(state="Loading Dataset")
        
        traces = []
        for i, tinf in enumerate(self.cache.iter_raw()):
            traces.append(tinf.trace)
            progress.update(i)
        traces = np.array(traces)

        progress.update(i, state="Fitting Dataset")

        if self.cols == 1:
            self.cache.nrm_cache = self.scalers[0].transform(traces)

        else:
            fchanls = []
            for c, scaler in enumerate(self.scalers):
                fchanls.append(scaler.transform(traces[:, c]))
            ftraces = np.stack(fchanls, axis=1)
            self.cache.nrm_cache = ftraces

        self.fitted = True
        progress.stop(i+1)

    def do_fit(self, index):
        return self.cache.nrm_cache[index]

    def fit(self, index):
        if not self.trained: self.train()
        if not self.fitted:  self.fit_all()
        return self.do_fit(index)

