#!/usr/bin/env python3

"""
The script used to load the dataset from the original source.
"""


import os
from collections import defaultdict

import json
import datasets

DATASET_PATH = None

_CITATION = """\
@inproceedings{bao2018table, 
    title={Table-to-Text: Describing Table Region with Natural Language}, 
    author={Junwei Bao and Duyu Tang and Nan Duan and Zhao Yan and Yuanhua Lv and Ming Zhou and Tiejun Zhao}, 
    booktitle={AAAI}, 
    url={https://www.aaai.org/ocs/index.php/AAAI/AAAI18/paper/download/16138/16782}, 
    year={2018} 
}
"""

_DESCRIPTION = """\
WikiTableText contains 5,000 tables from Wikipedia, each of which has at least 3 rows and 2 columns. 
For each table, three rows are selected resulting in 15,000 rows that are further used for manual annotation."""

_URL = "https://github.com/msra-nlc/Table2Text"
_LICENSE = "CC BY 4.0"


class WikiTableText(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "headers": datasets.Value("string"),
                    "content": datasets.Value("string"),
                    "row_number": datasets.Value("string"),
                    "reference": datasets.Value("string"),
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
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"split": "train"}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"split": "dev"}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"split": "test"}),
        ]

    def _normalize(self, lst):
        lst = lst.split("_||_")
        lst = [x.replace("_$$_", " ") for x in lst]
        lst = [x.replace("_", "").strip() for x in lst]

        return lst

    def _generate_examples(self, split):
        """Yields examples."""
        id_ = 0

        with open(DATASET_PATH + "/" + f"MSRA_NLC.Table2Text.{split}") as f:
            for line in f.readlines():
                items = line.split("\t")
                e = {
                    "row_number": items[0],
                    "headers": self._normalize(items[1]),
                    "content": self._normalize(items[2]),
                    "reference": self._normalize(items[3])[0],
                }

                id_ += 1
                yield id_, e


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/wikitabletext")
