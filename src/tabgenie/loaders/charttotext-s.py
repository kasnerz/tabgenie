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
import ast

from collections import defaultdict, namedtuple
from datasets import load_dataset
from .data import Cell, Table, HFTabularDataset
from ..utils.text import normalize

from tinyhtml import h


class ChartToTextS(HFTabularDataset):
    """
    The "Statista" subset of the Chart-To-Text dataset: https://github.com/vis-nlp/Chart-to-text/tree/main/statista_dataset/dataset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_content = {}
        self.hf_id = "kasnerz/charttotext-s"
        self.name = "Chart-to-Text (Statista subset)"

    def prepare_table(self, split, table_idx):
        t = Table()
        entry = self.data[split][table_idx]

        t.set_generated_output("reference", entry["ref"])
        t.props["title"] = entry["title"]

        for i, row in enumerate(ast.literal_eval(entry["content"])):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        return t
