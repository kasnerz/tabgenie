#!/usr/bin/env python3

"""
The script used to load the dataset from the original source.
"""

import os
import xml.etree.cElementTree as ET
from collections import defaultdict
from glob import glob
from os.path import join as pjoin
from pathlib import Path

import datasets

DATASET_PATH = None

_CITATION = """\
@inproceedings{van2020cacapo,
  title={The CACAPO dataset: A multilingual, multi-domain dataset for neural pipeline and end-to-end data-to-text generation},
  author={van der Lee, Chris and Emmery, Chris and Wubben, Sander and Krahmer, Emiel},
  booktitle={Proceedings of the 13th International Conference on Natural Language Generation},
  pages={68--79},
  year={2020}
}
"""

_DESCRIPTION = """\
CACAPO is a data-to-text dataset that contains sentences from news reports for the sports, weather, stock, and incidents domain in English and Dutch, aligned with relevant attribute-value paired data. This is the first data-to-text dataset based on "naturally occurring" human-written texts (i.e., texts that were not collected in a task-based setting), that covers various domains, as well as multiple languages. """
_URL = "https://github.com/TallChris91/CACAPO-Dataset"
_LICENSE = "CC BY 4.0"


def et_to_dict(tree):
    dct = {tree.tag: {} if tree.attrib else None}
    children = list(tree)
    if children:
        dd = defaultdict(list)
        for dc in map(et_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        dct = {tree.tag: dd}
    if tree.attrib:
        dct[tree.tag].update((k, v) for k, v in tree.attrib.items())
    if tree.text:
        text = tree.text.strip()
        if children or tree.attrib:
            if text:
                dct[tree.tag]["text"] = text
        else:
            dct[tree.tag] = text
    return dct


def parse_entry(entry):
    res = {}
    otriple_set_list = entry["originaltripleset"]
    res["original_triple_sets"] = [{"otriple_set": otriple_set["otriple"]} for otriple_set in otriple_set_list]
    mtriple_set_list = entry["modifiedtripleset"]
    res["modified_triple_sets"] = [{"mtriple_set": mtriple_set["mtriple"]} for mtriple_set in mtriple_set_list]
    res["category"] = entry["category"]
    res["eid"] = entry["eid"]
    res["size"] = int(entry["size"])
    res["lex"] = {
        "comment": [ex.get("comment", "") for ex in entry.get("lex", [])],
        "lid": [ex.get("lid", "") for ex in entry.get("lex", [])],
        "text": [ex.get("text", "") for ex in entry.get("lex", [])],
    }
    return res


def xml_file_to_examples(filename):
    tree = ET.parse(filename).getroot()

    examples = et_to_dict(tree)["benchmark"]["entries"][0]["entry"]
    return [parse_entry(entry) for entry in examples]


class CACAPO(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "category": datasets.Value("string"),
                    "lang": datasets.Value("string"),
                    "size": datasets.Value("int32"),
                    "eid": datasets.Value("string"),
                    "original_triple_sets": datasets.Sequence(
                        {"otriple_set": datasets.Sequence(datasets.Value("string"))}
                    ),
                    "modified_triple_sets": datasets.Sequence(
                        {"mtriple_set": datasets.Sequence(datasets.Value("string"))}
                    ),
                    "lex": datasets.Sequence(
                        {
                            "comment": datasets.Value("string"),
                            "lid": datasets.Value("string"),
                            "text": datasets.Value("string"),
                        }
                    ),
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
                name=datasets.Split.TRAIN,
                gen_kwargs={"filedirs": ["Incidents", "Sports", "Stocks", "Weather"], "split": "train"},
            ),
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={"filedirs": ["Incidents", "Sports", "Stocks", "Weather"], "split": "dev"},
            ),
            datasets.SplitGenerator(
                name=datasets.Split.TEST,
                gen_kwargs={"filedirs": ["Incidents", "Sports", "Stocks", "Weather"], "split": "test"},
            ),
        ]

    def _generate_examples(self, filedirs, split):
        """Yields examples."""
        id_ = 0

        for lang in ["en", "nl"]:
            for filedir in filedirs:
                xml_file = os.path.join(DATASET_PATH, lang, filedir, f"WebNLGFormat{split.title()}.xml")

                for exple_dict in xml_file_to_examples(xml_file):
                    exple_dict["category"] = filedir
                    exple_dict["lang"] = lang
                    id_ += 1
                    yield id_, exple_dict


if __name__ == "__main__":
    dataset = datasets.load_dataset(__file__)
    dataset.push_to_hub("kasnerz/cacapo")
