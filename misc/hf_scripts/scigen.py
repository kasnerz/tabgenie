"""Scigen: dataset for reasoning-aware data-to-text generation from scientific tables"""

import json
import datasets
import glob
import os

DATASET_PATH = None

_CITATION = """\
@article{moosavi:2021:SciGen,
  author    = {Nafise Sadat Moosavi, Andreas R{\"u}ckl{\'e}, Dan Roth, Iryna Gurevych},
  title     = {Learning to Reason for Text Generation from Scientific Tables},
  journal   = {arXiv preprint arXiv:2104.08296},
  year      = {2021},
  url       = {https://arxiv.org/abs/2104.08296}
}
"""
_DESCRIPTION = """\
SciGen is dataset for the task of reasoning-aware data-to-text generation consisting of tables from scientific articles and their corresponding descriptions.
"""

_URL = "https://github.com/UKPLab/SciGen"
_LICENSE = "CC BY-NC-SA 4.0"


class SciGen(datasets.GeneratorBasedBuilder):
    VERSION = "1.0.0"

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "paper": datasets.Value(dtype="string"),
                    "paper_id": datasets.Value(dtype="string"),
                    "table_caption": datasets.Value(dtype="string"),
                    "table_column_names": datasets.Value(dtype="large_string"),
                    "table_content_values": datasets.Value(dtype="large_string"),
                    "text": datasets.Value(dtype="large_string"),
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
        data_dir = "development" if split == "dev" else split

        if split in ["train", "dev"]:
            file_path = os.path.join(filepath, data_dir, "medium", f"{split}.json")
        else:
            # there is also "test-Other.json", should be looked into
            file_path = os.path.join(filepath, data_dir, f"test-CL.json")

        with open(file_path) as f:
            j = json.load(f)
            for example_idx, entry in enumerate(list(j.values())):
                yield example_idx, {key: str(value) for key, value in entry.items()}


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/scigen")
