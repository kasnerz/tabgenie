#!/usr/bin/env python3

"""NumericNLG: Towards Table-to-Text Generation with Numerical Reasoning"""

import json
import datasets
import glob
import os

DATASET_PATH = None

_CITATION = """\
@inproceedings{suadaa-etal-2021-towards,
    title = "Towards Table-to-Text Generation with Numerical Reasoning",
    author = "Suadaa, Lya Hulliyyatus  and
      Kamigaito, Hidetaka  and
      Funakoshi, Kotaro  and
      Okumura, Manabu  and
      Takamura, Hiroya",
    booktitle = "Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.acl-long.115",
    doi = "10.18653/v1/2021.acl-long.115",
    pages = "1451--1465"
}
"""
_DESCRIPTION = """\
NumericNLG is a dataset for table-totext generation focusing on numerical reasoning. 
The dataset consists of textual descriptions of numerical tables from scientific papers.
"""

_URL = "https://github.com/titech-nlp/numeric-nlg"
_LICENSE = "CC BY-SA 4.0"

DATASET_PATH = None


class NumericNLG(datasets.GeneratorBasedBuilder):
    VERSION = "1.0.0"

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "table_id_paper": datasets.Value(dtype="string"),
                    "caption": datasets.Value(dtype="string"),
                    "row_header_level": datasets.Value(dtype="int32"),
                    "row_headers": datasets.Value(dtype="large_string"),
                    "column_header_level": datasets.Value(dtype="int32"),
                    "column_headers": datasets.Value(dtype="large_string"),
                    "contents": datasets.Value(dtype="large_string"),
                    "metrics_loc": datasets.Value(dtype="string"),
                    "metrics_type": datasets.Value(dtype="large_string"),
                    "target_entity": datasets.Value(dtype="large_string"),
                    "table_html_clean": datasets.Value(dtype="large_string"),
                    "table_name": datasets.Value(dtype="string"),
                    "table_id": datasets.Value(dtype="string"),
                    "paper_id": datasets.Value(dtype="string"),
                    "page_no": datasets.Value(dtype="int32"),
                    "dir": datasets.Value(dtype="string"),
                    "description": datasets.Value(dtype="large_string"),
                    "class_sentence": datasets.Value(dtype="string"),
                    "sentences": datasets.Value(dtype="large_string"),
                    "header_mention": datasets.Value(dtype="string"),
                    "valid": datasets.Value(dtype="int32"),
                }
            ),
            supervised_keys=None,
            homepage="https://github.com/titech-nlp/numeric-nlg",
            citation=_CITATION,
            license=_LICENSE,
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "train"},
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "dev"},
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={"filepath": DATASET_PATH + "/" + "data", "split": "test"},
            ),
        ]

    def _generate_examples(self, filepath, split):
        filename = split if split != "dev" else "val"

        with open(os.path.join(filepath, f"table_{filename}.json")) as f:
            j_tables = json.load(f)

        with open(os.path.join(filepath, f"table_desc_{filename}.json")) as f:
            j_desc = json.load(f)

        for example_idx, (entry, desc) in enumerate(zip(j_tables, j_desc)):

            assert entry["table_id_paper"] == desc["table_id_paper"]

            e = {key: str(value) for key, value in entry.items()}

            for key in ["description", "class_sentence", "header_mention", "sentences"]:
                e[key] = str(desc[key])

            yield example_idx, e


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)

    dataset.push_to_hub("kasnerz/numericnlg")
