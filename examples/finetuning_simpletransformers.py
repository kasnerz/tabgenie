#!/usr/bin/env python3

from simpletransformers.seq2seq import Seq2SeqModel, Seq2SeqArgs
import tabgenie as tg
import pandas as pd
import torch

# import resource
# rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
# resource.setrlimit(resource.RLIMIT_NOFILE, (100, rlimit[1]))


dataset_name = "webnlg"
tg_dataset = tg.load_dataset(dataset_name)

model_args = {
    "num_train_epochs": 10,
    "evaluate_generated_text": True,
    "evaluate_during_training": True,
    "evaluate_during_training_verbose": True,
    "output_dir": "experiments",
    "overwrite_output_dir": True,
    "use_cuda": torch.cuda.is_available(),
    "use_multiprocessing": False,
    "no_cache": True,
    "learning_rate": 2e-5,
    "adam_betas": (0.9, 0.997),
    "adam_epsilon": 1e-9,
    "n_gpu": 1
}

model = Seq2SeqModel(encoder_decoder_type="bart", encoder_decoder_name="facebook/bart-base", args=model_args)

dataset = {}

for split in ["train", "dev", "test"]:
    data = tg_dataset.get_linearized_pairs(split)
    dataset[split] = pd.DataFrame(data, columns=["input_text", "target_text"])

model.train_model(dataset["train"], eval_data=dataset["dev"])
result = model.eval_model(dataset["test"])

print(result)
