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
from tinyhtml import h

logger = logging.getLogger(__name__)


def get_dataset_class_by_name(dataset_name):
    dataset_mapping = {
        "dart": "DART",
        "e2e": "E2E",
        "hitab": "HiTab",
        "charttotext-s": "ChartToTextS",
        "logic2text": "Logic2Text",
        "logicnlg": "LogicNLG",
        "numericnlg": "NumericNLG",
        "scigen": "SciGen",
        "sportsett": "SportSettBasketball",
        "webnlg": "WebNLG",
        "wikibio": "WikiBio",
        "totto": "ToTTo",
    }
    dataset_module = __import__(
        dataset_name,
        globals=globals(),
        fromlist=[dataset_mapping[dataset_name]],
        level=1,
    )
    dataset_class = getattr(dataset_module, dataset_mapping[dataset_name])
    return dataset_class


class Cell:
    """
    Table cell
    """

    def __init__(self, value=None):
        self.idx = None
        self.value = value
        self.colspan = 1
        self.rowspan = 1
        self.is_highlighted = False
        self.is_col_header = False
        self.is_row_header = False
        self.is_dummy = False

    def is_header(self):
        return self.is_col_header or self.is_row_header

    def __repr__(self):
        return str(self.__dict__)


class Table:
    """
    Table object
    """

    def __init__(self):
        self.title = None
        self.extra_headers = []
        self.cells = []
        self.ref = None
        self.url = None
        self.cell_idx = 0
        self.current_row = []

    def save_row(self):
        if self.current_row:
            self.cells.append(self.current_row)
            self.current_row = []

    def add_cell(self, cell):
        cell.idx = self.cell_idx
        self.current_row.append(cell)
        self.cell_idx += 1

    def set_cell(self, i, j, c):
        self.cells[i][j] = c

    def get_cell(self, i, j):
        try:
            return self.cells[i][j]
        except:
            return None

    def get_cell_by_id(self, idx):
        for row in self.cells:
            for c in row:
                if c.idx == idx:
                    return c

        return None

    def __repr__(self):
        return str(self.__dict__)


class TabularDataset:
    """
    Base class for the datasets
    """

    def __init__(self, path):
        self.splits = ["train", "dev", "test"]
        self.data = {split: [] for split in self.splits}
        self.tables = {split: {} for split in self.splits}
        self.path = path

    def load(self, split, max_examples=None):
        """
        Load the dataset. Path can be specified for loading from a directory
        or omitted if the dataset is loaded from HF.
        """
        raise NotImplementedError

    def get_reference(self, split, index):
        t = self.get_table(split, index)
        return t.ref

    def has_split(self, split):
        return bool(self.data[split])

    def get_table(self, split, index):
        table = self.tables[split].get(index)

        if not table:
            table = self.prepare_table(split, index)

        return table

    def prepare_table(self, split, index):
        return NotImplementedError

    def get_generation_input(self, split, table_idx, cell_ids):
        t = self.get_table(split, table_idx)
        cells = [t.get_cell_by_id(int(idx)) for idx in cell_ids]
        gen_input = []

        if t.title:
            gen_input.append("[TITLE] " + t.title)

        for c in cells:
            gen_input.append("[CELL] " + c.value + " [/CELL]")

        return " ".join(gen_input)

    def get_table_html(self, split, index):
        t = self.get_table(split, index)
        headers = []

        if t.title:
            title_el = h("p")(h("h5")(t.title))
            if t.url:
                title_el = h("p")(h("a", href=t.url)(title_el))
            headers.append(title_el)

        for extra_header in t.extra_headers:
            headers.append(h("p")(h("b")(extra_header)))

        header_el = h("div")(headers)
        trs = []

        for row in t.cells:
            tds = []
            for c in row:
                if c.is_dummy:
                    continue

                eltype = "th" if c.is_header() else "td"
                td_el = h(eltype, colspan=c.colspan, rowspan=c.rowspan, cell_idx=c.idx)(
                    c.value
                )

                if c.is_highlighted:
                    td_el.tag.attrs["class"] = "table-active"

                tds.append(td_el)
            trs.append(tds)

        tbodies = [h("tr")(tds) for tds in trs]
        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(
            lxml.html.fromstring(html), encoding="unicode", pretty_print=True
        )


class HFTabularDataset(TabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = None #TODO set
        self.hf_extra_config = None
        self.split_mapping = {
            "train" : "train",
            "dev" : "validation",
            "test" : "test"
        }

    def load(self, split, max_examples=None):
        hf_split = self.split_mapping[split]

        try:
            dataset = datasets.load_dataset(self.hf_id, name=self.hf_extra_config, split=datasets.ReadInstruction(hf_split, to=max_examples+1, unit='abs'))
        except AssertionError:
            # max_examples is set higher than the total number of examples in the dataset
            dataset = datasets.load_dataset(self.hf_id, name=self.hf_extra_config, split=hf_split)
        
        self.data[split] = dataset
