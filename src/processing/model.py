#!/usr/bin/env python3
import logging
import numpy as np
import os

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

try:
    import torch
    import pytorch_lightning as pl
    from nlg.inference import Seq2SeqInferenceModule
except:
    logger.warning(
        "Model related modules not found. This is ok if you are running the app in light mode."
    )


class Dict2Obj:
    def __init__(self, entries):
        self.__dict__.update(entries)


class Model:
    def __init__(self, seed=42, max_threads=8):
        self.seed = seed
        self.max_threads = max_threads

    def load(self, exp_dir, experiment, checkpoint="model.ckpt"):
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        torch.set_num_threads(self.max_threads)

        model_path = os.path.join(exp_dir, experiment, checkpoint)
        args = Dict2Obj({"beam_size": 1, "gpus": 1, "max_length": 1024})
        self.dm = Seq2SeqInferenceModule(args=args, model_path=model_path)

    def generate(self, s):
        out = self.dm.predict(s)
        return out


# if __name__ == "__main__":
#     m = Model()
#     m.load(
#         exp_dir="/lnet/work/people/kasner/projects/ng-nlg/experiments",
#         experiment="webnlg"
#     )
#     print(m.generate("Prague | capital | Czechia"))
