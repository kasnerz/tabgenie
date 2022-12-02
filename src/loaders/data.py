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
        self.headers = {}
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
        # TODO improve
        for row in self.cells:
            for c in row:
                if c.idx == idx:
                    return c

        return None

    def get_flat_cells(self):
        return [x for row in self.cells for x in row]

    def get_cells(self):
        return self.cells

    def get_row_headers(self, row_idx):
        try:
            cells_in_row = self.cells[row_idx]
            return [x for x in cells_in_row if x.is_row_header]
        except Exception as e:
            logger.exception(e)

    def get_col_headers(self, column_idx):
        try:
            cells_in_column = [row[column_idx] for row in self.cells]
            return [x for x in cells_in_column if x.is_col_header]
        except Exception as e:
            logger.exception(e)

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
        self.dataset_info = {}
        self.name = None

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

    def get_info(self):
        return self.dataset_info

    def _export_linear(self, split, table_idx, cell_ids):
        t = self.get_table(split, table_idx)

        if cell_ids:
            cells = [t.get_cell_by_id(int(idx)) for idx in cell_ids]
        else:
            cells = t.get_flat_cells()

        gen_input = []

        for key, value in t.headers.items():
            gen_input.append(f"[{key}] {value}")

        for c in cells:
            gen_input.append("[cell] " + c.value)

        return " ".join(gen_input)

    def _export_triples(self, split, table_idx, cell_ids):
        # default method (dataset-agnostic)
        t = self.get_table(split, table_idx)
        title = t.headers.get("title")
        triples = []

        for i, row in enumerate(t.get_cells()):
            for j, cell in enumerate(row):
                if cell.is_header():
                    continue
                
                row_headers = t.get_row_headers(i)
                col_headers = t.get_col_headers(j)

                if row_headers and col_headers:
                    subj = row_headers[0].value
                    pred = col_headers[0].value

                elif row_headers and not col_headers:
                    subj = title
                    pred = row_headers[0].value
                
                elif col_headers and not row_headers:
                    subj = title
                    pred = col_headers[0].value

                obj = cell.value
                triples.append([subj, pred, obj])

        return triples


    def export_table(self, split, table_idx, export_format):
        cell_ids = None # TODO implement

        if export_format == "linearize":
            inp = self._export_linear(split, table_idx, cell_ids)
        elif export_format == "triples":
            inp = self._export_triples(split, table_idx, cell_ids)
        elif export_format == "html":
            inp = self.get_table_html(split, table_idx)
        else:
            raise NotImplementedError(export_format)

        return inp
        # out = self.get_table(split, table_idx).ref

        # return {
        #     "in" : inp,
        #     "out" : out
        # }
    
    def export(self, split, table_idxs=None, export_format="linearize"):
        return self.export_table(split, table_idxs[0], export_format)
        # data = {"data" : []}

        # if table_idxs is None:
        #     table_idxs = range(len(self.tables))
        
        # for table_idx in table_idxs:
        #     example = self.export_table(split, table_idx, export_format)
        #     data["data"].append(example)

        # return data

    def get_table_html(self, split, index):
        t = self.get_table(split, index)

        if t.headers:
            meta_trs = []
            for key, value in t.headers.items():
                meta_trs.append([h("th")(key), h("td")(value)])

            meta_tbodies = [h("tr")(tds) for tds in meta_trs]
            meta_tbody_el = h("tbody")(meta_tbodies)
            meta_table_el = h("table", klass="table table-sm caption-top meta-table")(h("caption")("properties"),meta_tbody_el)
            
            # meta_table_el = h("div")(h("h5")("Meta"), meta_table_el)
        else: 
            meta_table_el = None

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
        table_el = h("table", klass="table table-sm table-bordered caption-top main-table")(h("caption")("data"), tbody_el)
        # table_el = h("div")(h("h5")("Data"), table_el)
        area_el = h("div")(meta_table_el, table_el)

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
        self.dataset_info = {}

    def load(self, split, max_examples=None):
        hf_split = self.split_mapping[split]

        try:
            dataset = datasets.load_dataset(self.hf_id, name=self.hf_extra_config, split=datasets.ReadInstruction(hf_split, to=max_examples+1, unit='abs'))
        except (AssertionError, ValueError, TypeError):
            # max_examples is set higher than the total number of examples in the dataset
            dataset = datasets.load_dataset(self.hf_id, name=self.hf_extra_config, split=hf_split)
        
        self.dataset_info = dataset.info.__dict__
        self.data[split] = dataset

    def get_info(self):
        info = {key: self.dataset_info[key] for key in ["citation", "description", "homepage"]}
        info["name"] = self.name

        return info