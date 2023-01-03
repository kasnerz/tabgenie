#!/usr/bin/env python3
import logging
import numpy as np
import os
import torch
from nlg.inference import Seq2SeqInferenceModule

from ..processing import Processor

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

class Dict2Obj:
    def __init__(self, entries):
        self.__dict__.update(entries)

class ModelLocalProcessor(Processor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.info("Loading model...")
        seed = 42
        torch.manual_seed(seed)
        np.random.seed(seed)
        torch.set_num_threads(8)

        exp_dir="/lnet/work/people/kasner/projects/ng-nlg/experiments"
        experiment="totto"
        checkpoint="model.ckpt"

        model_path = os.path.join(exp_dir, experiment, checkpoint)
        model_args = Dict2Obj({"beam_size": 1, "gpus": 1, "max_length": 1024})
        self.dm = Seq2SeqInferenceModule(args=model_args, model_path=model_path)


    def process(self, content):
        out = self.dm.predict(content)[0]
        return self.text2html(out)
