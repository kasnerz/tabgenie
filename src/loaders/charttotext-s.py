#!/usr/bin/env python3
import json
import csv
import os
import logging
import re
import random
import datasets
import pandas as pd
import lxml.etree
import lxml.html
import glob

from collections import defaultdict, namedtuple
from datasets import load_dataset
from .data import Cell, Table, TabularDataset
from ..utils.text import normalize

from tinyhtml import h


class ChartToTextS(TabularDataset):
    """
    The "Statista" subset of the Chart-To-Text dataset: https://github.com/vis-nlp/Chart-to-text/tree/main/statista_dataset/dataset
    """

    name = "charttotext-s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_content = {}

    def prepare_table(self, split, index):
        t = Table()
        entry = self.data[split][index]

        t.ref = entry["ref"]
        t.title = entry["title"]

        for i, row in enumerate(entry["content"]):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t

    def load(self, split):
        mapping_file = split if split != "dev" else "val"

        with open(
            os.path.join(
                self.path, "dataset_split", f"{mapping_file}_index_mapping.csv"
            )
        ) as f:
            next(f)
            for line in f:
                subdir = "." if line.startswith("two_col") else "multiColumn"
                filename = line.split("-")[1].split(".")[0]

                with open(
                    os.path.join(self.path, subdir, "data", filename + ".csv")
                ) as g:
                    content = []
                    reader = csv.reader(g, delimiter=",", quotechar='"')
                    for row in reader:
                        content.append(row)

                with open(
                    os.path.join(self.path, subdir, "captions", filename + ".txt")
                ) as g:
                    ref = g.read().rstrip("\n")

                with open(
                    os.path.join(self.path, subdir, "titles", filename + ".txt")
                ) as g:
                    title = g.read().rstrip("\n")

                self.data[split].append(
                    {"content": content, "ref": ref, "title": title}
                )
