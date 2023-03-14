#!/usr/bin/env python3

"""
The script used to load the dataset from the original source.
"""

import json
import datasets
import os
import csv

DATASET_PATH = None

_CITATION = """\
@inproceedings{kantharaj2022chart,
  title={Chart-to-Text: A Large-Scale Benchmark for Chart Summarization},
  author={Kantharaj, Shankar and Leong, Rixie Tiffany and Lin, Xiang and Masry, Ahmed and Thakkar, Megh and Hoque, Enamul and Joty, Shafiq},
  booktitle={Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  pages={4005--4023},
  year={2022}
}
"""
_DESCRIPTION = """\
Chart-to-Text is a large-scale benchmark with two datasets and a total of 44,096 charts covering a wide range of topics and chart types.
This dataset CONTAINS ONLY the Statista subset from the benchmark. 
Statista (statista.com) is an online platform that regularly publishes charts on a wide range of topics including economics, market and opinion research.

Statistics:
Total charts: 27868

=== Chart Type Information ===
Number of charts of each chart type
column: 16319
bar: 8272
line: 2646
pie: 408
table: 223

=== Token Information ===
Average token count per summary: 53.65027989091431
Total tokens: 1495126
Total types (unique tokens): 39598
=== Sentence Information ===
Average sentence count per summary: 2.5596741782689825
"""

_URL = "https://github.com/vis-nlp/Chart-to-text/tree/main/statista_dataset/dataset"
_LICENSE = "GNU General Public License v3.0"


class ChartToTextS(datasets.GeneratorBasedBuilder):
    VERSION = "1.0.0"

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "title": datasets.Value(dtype="string"),
                    "ref": datasets.Value(dtype="string"),
                    "content": datasets.Value(dtype="large_string"),
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
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "train"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "dev"}
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST, gen_kwargs={"filepath": DATASET_PATH + "/" + "dataset", "split": "test"}
            ),
        ]

    def _generate_examples(self, filepath, split):
        data = []
        mapping_file = split if split != "dev" else "val"

        with open(os.path.join(filepath, "dataset_split", f"{mapping_file}_index_mapping.csv")) as f:
            next(f)
            for i, line in enumerate(f):
                subdir = "." if line.startswith("two_col") else "multiColumn"
                filename = line.split("-")[1].split(".")[0]

                with open(os.path.join(filepath, subdir, "data", filename + ".csv")) as g:
                    content = []
                    reader = csv.reader(g, delimiter=",", quotechar='"')
                    for row in reader:
                        content.append(row)

                with open(os.path.join(filepath, subdir, "captions", filename + ".txt")) as g:
                    ref = g.read().rstrip("\n")

                with open(os.path.join(filepath, subdir, "titles", filename + ".txt")) as g:
                    title = g.read().rstrip("\n")

                data.append({"content": content, "ref": ref, "title": title})

                if i % 1000 == 0:
                    print(f"Loaded {i} items")

        for example_idx, entry in enumerate(data):
            yield example_idx, {key: str(value) for key, value in entry.items()}


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/charttotext-s")
