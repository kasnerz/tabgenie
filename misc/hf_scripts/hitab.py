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
@article{cheng2021hitab,
  title={HiTab: A Hierarchical Table Dataset for Question Answering and Natural Language Generation},
  author={Cheng, Zhoujun and Dong, Haoyu and Wang, Zhiruo and Jia, Ran and Guo, Jiaqi and Gao, Yan and Han, Shi and Lou, Jian-Guang and Zhang, Dongmei},
  journal={arXiv preprint arXiv:2108.06712},
  year={2021}
}
"""
_DESCRIPTION = """\
HiTab is a dataset for question answering and data-to-text over hierarchical tables. It contains 10,672 samples and 3,597 tables from statistical reports (StatCan, NSF) and Wikipedia (ToTTo). 98.1% of the tables in HiTab are with hierarchies.
"""

_URL = "https://github.com/microsoft/HiTab"
_LICENSE = "C-UDA 1.0"


class HiTab(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("2022.2.7")

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value(dtype="string"),
                    "table_id": datasets.Value(dtype="string"),
                    "table_source": datasets.Value(dtype="string"),
                    "sentence_id": datasets.Value(dtype="string"),
                    "sub_sentence_id": datasets.Value(dtype="string"),
                    "sub_sentence": datasets.Value(dtype="string"),
                    "question": datasets.Value(dtype="string"),
                    "answer": datasets.Value(dtype="large_string"),
                    "aggregation": datasets.Value(dtype="large_string"),
                    "linked_cells": datasets.Value(dtype="large_string"),
                    "answer_formulas": datasets.Value(dtype="large_string"),
                    "reference_cells_map": datasets.Value(dtype="large_string"),
                    "table_content": datasets.Value(dtype="large_string"),
                }
            ),
            supervised_keys=None,
            homepage="https://www.microsoft.com/en-us/research/publication/hitab-a-hierarchical-table-dataset-for-question-answering-and-natural-language-generation/",
            citation=_CITATION,
            license=_LICENSE,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "train"}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "dev"}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "test"}),
        ]

    def _generate_examples(self, filepath, split):
        table_content = {}
        data = []

        for filename in glob.glob(os.path.join(filepath, "tables", "raw", "*.json")):
            with open(filename) as f:
                j = json.load(f)
                table_name = os.path.basename(filename).rstrip(".json")
                table_content[table_name] = j

        with open(os.path.join(filepath, f"{split}_samples.jsonl")) as f:
            for i, line in enumerate(f.readlines()):
                j = json.loads(line)
                data.append(j)

        for example_idx, entry in enumerate(data):
            entry["table_content"] = table_content.get(entry["table_id"])
            yield example_idx, {key: str(value) for key, value in entry.items()}


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/hitab")
