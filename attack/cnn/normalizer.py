###############################################################################
# File        : normalizer.py
# Author      : kareem
# Created     : 2025 Nov 06
# Description : Normalizing structure (and also trace cache)
###############################################################################

import numpy as np
from sklearn.preprocessing import RobustScaler

## Generic Constructor -------------------------------------

def build_normalizer(cache, nparams):
    match nparams['norm']:
        case None     : return NOPNormalizer(cache, nparams)
        case "scale"  : return ScaleNormalizer(cache, nparams)
        case "robust" : return RobustNormalizer(cache, nparams)
        case _        : raise NotImplementedError(f"Unknown normalization technique {nparams['norm']}")

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
        self.mult = params["mult"]

    def do_fit(self, index): return self.cache.raw_cache[index].trace * self.mult

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
        traces = np.array([tinf.trace for tinf in self.cache.iter_raw()])

        if self.cols == 1:
            scaler = RobustScaler(quantile_range=(10, 90))
            scaler.fit(traces)
            self.scalers = [scaler]
            # print(scaler.center_, scaler.scale_)

        else:
            self.fchanls = []
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

    def load_training(self, them):
        super().load_training(them)
        self.scalers = them.scalers
        self.trained = True
        self.fitted = False

    def fit_all(self):
        traces = np.array([tinf.trace for tinf in self.cache.iter_raw()])

        if self.cols == 1:
            self.cache.nrm_cache = self.scalers[0].transform(traces)

        else:
            fchanls = []
            for c, scaler in enumerate(self.scalers):
                fchanls.append(scaler.transform(traces[:, c]))
            ftraces = np.stack(fchanls, axis=1)
            self.cache.nrm_cache = ftraces

        self.fitted = True

    def do_fit(self, index):
        return self.cache.nrm_cache[index]

    def fit(self, index):
        if not self.trained: self.train()
        if not self.fitted:  self.fit_all()
        return self.do_fit(index)

