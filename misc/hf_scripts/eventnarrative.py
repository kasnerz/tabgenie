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
@inproceedings{colas2021eventnarrative,
  title={EventNarrative: A Large-scale Event-centric Dataset for Knowledge Graph-to-Text Generation},
  author={Colas, Anthony and Sadeghian, Ali and Wang, Yue and Wang, Daisy Zhe},
  booktitle={Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 1)},
  year={2021}
}
"""

_DESCRIPTION = """\
EventNarrative is a knowledge graph-to-text dataset from publicly available open-world knowledge graphs, focusing on event-centric data. 
EventNarrative consists of approximately 230,000 graphs and their corresponding natural language text, 6 times larger than the current largest parallel dataset. 
It makes use of a rich ontology and all of the KGs entities are linked to the text."""

_URL = "https://www.kaggle.com/datasets/acolas1/eventnarration"
_LICENSE = "CC BY 4.0"


class EventNarrative(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "Event_Name": datasets.Value("string"),
                    "entity_ref_dict": datasets.Value("large_string"),
                    "keep_triples": datasets.Value("large_string"),
                    "narration": datasets.Value("large_string"),
                    "types": datasets.Value("string"),
                    "wikipediaLabel": datasets.Value("string"),
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

    def _generate_examples(self, split):
        """Yields examples."""
        id_ = 0

        with open(DATASET_PATH + "/" + f"{split}_data.json") as f:
            j = json.load(f)

            for example in j:
                e = {key: str(value) for key, value in example.items()}
                id_ += 1
                yield id_, e


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)

    import pdb

    pdb.set_trace()  # breakpoint ffb6df83 //

    # dataset.push_to_hub("kasnerz/eventnarrative")
