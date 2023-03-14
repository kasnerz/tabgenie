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
@inproceedings{chen2020logical,
  title={Logical Natural Language Generation from Open-Domain Tables},
  author={Chen, Wenhu and Chen, Jianshu and Su, Yu and Chen, Zhiyu and Wang, William Yang},
  booktitle={Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics},
  pages={7929--7942},
  year={2020}
}
"""
_DESCRIPTION = """\
LogicNLG is a dataset for natural language generation from open-domain tables. 
LogicNLG is based on TabFact (Chen et al., 2019), which is a table-based fact-checking dataset with rich logical inferences in the annotated statements.
"""

_URL = "https://github.com/wenhuchen/LogicNLG"
_LICENSE = "MIT"


class LogicNLG(datasets.GeneratorBasedBuilder):
    VERSION = "1.0.0"

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "table": datasets.Value(dtype="large_string"),
                    "ref": datasets.Value(dtype="string"),
                    "linked_columns": datasets.Value(dtype="string"),
                    "title": datasets.Value(dtype="string"),
                    "template": datasets.Value(dtype="string"),
                    "table_id": datasets.Value(dtype="string"),
                }
            ),
            supervised_keys=None,
            homepage="https://wenhuchen.github.io/logicnlg.github.io/",
            citation=_CITATION,
            license=_LICENSE,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "train"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "dev"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "test"}
            ),
        ]

    def _generate_examples(self, filepath, split):
        filename = split if split != "dev" else "val"
        data = []

        with open(os.path.join(filepath, f"{filename}_lm.json")) as f:
            j = json.load(f)

        for i, (table_id, examples) in enumerate(j.items()):
            table = []
            with open(os.path.join(filepath, "all_csv", table_id)) as f:
                for line in f.readlines():
                    table.append(line.rstrip("\n").split("#"))

            for example in examples:
                data.append(
                    {
                        "table": table,
                        "ref": example[0],
                        "linked_columns": example[1],
                        "title": example[2],
                        "template": example[3],
                        "table_id": table_id,
                    }
                )
        for example_idx, entry in enumerate(data):
            yield example_idx, {key: str(value) for key, value in entry.items()}


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/logicnlg")
