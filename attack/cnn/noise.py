import numpy as np

class NoiseGenerator:
    def __init__(self, method, rms):
        self.method = method
        self.rms = rms

    def gen(self, length):
        match self.method:
            case 'white-gaussian' : 
                arr = np.random.normal(0, self.rms, size=length)
                return arr.astype(np.float32)
            case _ : 
                raise NotImplementedError(f"Unsupported noise type {self.method}")

