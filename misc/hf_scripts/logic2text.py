#!/usr/bin/env python3

"""
The script used to load the dataset from the original source.
"""


import json
import datasets
import glob
import os

DATASET_PATH = None

_CITATION = """\
@inproceedings{chen2020logic2text,
  title={Logic2Text: High-Fidelity Natural Language Generation from Logical Forms},
  author={Chen, Zhiyu and Chen, Wenhu and Zha, Hanwen and Zhou, Xiyou and Zhang, Yunkai and Sundaresan, Sairam and Wang, William Yang},
  booktitle={Findings of the Association for Computational Linguistics: EMNLP 2020},
  pages={2096--2111},
  year={2020}
}
"""
_DESCRIPTION = """\
Logic2Text is a large-scale dataset with 10,753 descriptions involving common logic types paired with the underlying logical forms.
The logical forms show diversified graph structure of free schema, which poses great challenges on the model's ability to understand the semantics. 
"""

_URL = "https://github.com/czyssrs/Logic2Text"
_LICENSE = "MIT"


class Logic2Text(datasets.GeneratorBasedBuilder):
    VERSION = "1.0.0"

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "topic": datasets.Value(dtype="string"),
                    "wiki": datasets.Value(dtype="string"),
                    "url": datasets.Value(dtype="string"),
                    "action": datasets.Value(dtype="string"),
                    "sent": datasets.Value(dtype="string"),
                    "annotation": datasets.Value(dtype="string"),
                    "logic": datasets.Value(dtype="string"),
                    "logic_str": datasets.Value(dtype="string"),
                    "interpret": datasets.Value(dtype="string"),
                    "num_func": datasets.Value(dtype="string"),
                    "nid": datasets.Value(dtype="string"),
                    "g_ids": datasets.Value(dtype="string"),
                    "g_ids_features": datasets.Value(dtype="string"),
                    "g_adj": datasets.Value(dtype="string"),
                    "table_header": datasets.Value(dtype="string"),
                    "table_cont": datasets.Value(dtype="large_string"),
                }
            ),
            supervised_keys=None,
            homepage=_URL,
            citation=_CITATION,
            license=_LICENSE,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "train"}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "dev"}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "test"}),
        ]

    def _generate_examples(self, filepath, split):
        data = []
        filename = split if split != "dev" else "valid"

        with open(os.path.join(filepath, f"{filename}.json")) as f:
            data = json.load(f)

        for example_idx, entry in enumerate(data):
            yield example_idx, {key: str(value) for key, value in entry.items()}


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/logic2text")
