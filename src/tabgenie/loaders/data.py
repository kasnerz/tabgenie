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
import jinja2
import copy

from collections import defaultdict, namedtuple
from tabgenie.utils.text import format_prompt
from tinyhtml import h

logger = logging.getLogger(__name__)


def get_dataset_class_by_name(dataset_name):
    # todo kate: what for?
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
        "wikisql": "WikiSQL"
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
        self.props = {}
        self.cells = []
        self.outputs = {}
        self.url = None
        self.cell_idx = 0
        self.current_row = []
        self.cell_by_ids = {}

    def save_row(self):
        if self.current_row:
            self.cells.append(self.current_row)
            self.current_row = []

    def add_cell(self, cell):
        cell.idx = self.cell_idx
        self.current_row.append(cell)
        self.cell_by_ids[self.cell_idx] = cell
        self.cell_idx += 1
        
    def set_cell(self, i, j, c):
        self.cells[i][j] = c

    def get_cell(self, i, j):
        try:
            return self.cells[i][j]
        except:
            return None

    def get_cell_by_id(self, idx):
        return self.cell_by_ids[idx]

    def get_flat_cells(self, highlighted_only=False):
        return [x for row in self.cells for x in row if (x.is_highlighted or not highlighted_only)]

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

    def get_generated_output(self, key):
        return self.outputs.get(key)

    def get_generated_outputs(self):
        return [{"name" : key, "out" : val} for key, val in self.outputs.items()]

    def set_generated_output(self, key, value):
        self.outputs[key] = value

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

    def load_outputs(self, split, name):
        out_fname = os.path.join("outputs", self.name.lower(), split, name + ".out")

        # output does not exist for the dataset
        if not (os.path.isfile(out_fname)):
            logger.debug(out_fname + " does not exist")
            return

        with open(out_fname) as f:
            outputs = f.readlines()

            if len(outputs) != self.get_example_count(split):
                raise AssertionError(f"Length of the outputs from '{name}' and the number of examples in {self.name}/{split} do not agree: {len(outputs)} vs. {self.get_example_count(split)}")

            for o in outputs:
                self.tables.set_output(name, o)

    def get_reference(self, table):
        return table.get_generated_output("reference")

    def get_generated_outputs(self, table):
        return table.get_generated_outputs()

    def get_example_count(self, split):
        return len(self.data[split])

    def has_split(self, split):
        return bool(self.data[split])

    def get_table(self, split, table_idx, edited_cells=None):
        table = self.tables[split].get(table_idx)

        if not table:
            table = self.prepare_table(split, table_idx)
            self.tables[split][table_idx] = table

        if edited_cells:
            table_modif = copy.deepcopy(table)
            
            for cell_id, val in edited_cells.items():
                cell = table_modif.get_cell_by_id(int(cell_id))
                cell.value = val

            table = table_modif

        return table

    def prepare_table(self, split, table_idx):
        return NotImplementedError

    def get_info(self):
        return self.dataset_info

    def export_table(self, table, export_format, cell_ids=None):
        if export_format == "txt":
            exported = self.table_to_linear(table, cell_ids)
        elif export_format == "triples":
            exported = self.table_to_triples(table, cell_ids)
        elif export_format == "instruct":
            exported = self.table_to_instruct(table, cell_ids)
            exported = format_prompt(prompt=exported, table=table, dataset=self)
        elif export_format == "html":
            exported = self.table_to_html(table)
        elif export_format == "csv":
            exported = self.table_to_csv(table)
        elif export_format == "xlsx":
            exported = self.table_to_df(table)
        elif export_format == "reference":
            exported = self.get_reference(table)
        else:
            raise NotImplementedError(export_format)

        return exported


    def export(self, split, table_cfg):
        exported = []
        
        for i in range(self.get_example_count(split)):
            obj = {}
            for key, export_format in table_cfg["fields"].items():
                table = self.get_table(split, i)
                obj[key] = self.export_table(table, export_format=export_format)                
            exported.append(obj)

        return exported


    def table_to_linear(self, table, cell_ids=None):
        if cell_ids:
            cells = [table.get_cell_by_id(int(idx)) for idx in cell_ids]
        else:
            cells = table.get_flat_cells()

        gen_input = []

        for key, value in table.props.items():
            gen_input.append(f"[{key}] {value}")

        for c in cells:
            gen_input.append("[cell] " + c.value)

        return " ".join(gen_input)

    def table_to_triples(self, table, cell_ids):
        # default method (dataset-agnostic)
        title = table.props.get("title")
        triples = []

        for i, row in enumerate(table.get_cells()):
            for j, cell in enumerate(row):
                if cell.is_header():
                    continue
                
                row_headers = table.get_row_headers(i)
                col_headers = table.get_col_headers(j)

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
    

    def get_task_definition(self):
        # TODO implement for individual datasets
        return "Write a short description of the linearized table cells."

    def get_positive_examples(self):
        # TODO implement for individual datasets
        # TODO fix - split may not be loaded
        table_ex_1 = self.get_table("dev", 0)
        table_ex_2 = self.get_table("dev", 1)

        return [
            {
                "in" : self.table_to_linear(table_ex_1),
                "out" : self.get_reference(table_ex_1),
            },
            {
                "in" : self.table_to_linear(table_ex_2),
                "out" : self.get_reference(table_ex_2),
            }
        ]

    def get_prompt(self, key):
        prompts = {
            "tk-def-pos": "Definition: {definition}\n\nPositive Example 1 -\nInput:\n{{ex_1_in}} Output:\n{{ex_1_out}}\nPositive Example 2 -\nInput:\n{{ex_2_in}}\nOutput:\n{{ex_2_out}}\nNow complete the following example - \nInput:\n%table_txt%\nOutput:\n",
            "tk-def": "Definition: {definition}\n\nNow complete the following example - \nInput:\n%table_txt%\nOutput:\n",
            "totto" : "%table_txt%"
        }

        prompt = prompts[key]

        if "def" in key:
            definition = self.get_task_definition()
            prompt = prompt.format(definition=definition)

        if "pos" in key:
            ex = self.get_positive_examples()
            ex_1_in, ex_1_out, ex_2_in, ex_2_out = ex[0]["in"].strip(), ex[0]["out"].strip(), ex[1]["in"].strip(), ex[1]["out"].strip()
            prompt = prompt.format(ex_1_in=ex_1_in, ex_1_out=ex_1_out, ex_2_in=ex_2_in, ex_2_out=ex_2_out)

        return prompt


    def table_to_instruct(self, table, cell_ids):
        prompt = self.get_prompts()["tk-def-pos"]


        import pdb; pdb.set_trace();
        if "%table_csv%" in prompt:
            df = self.table_to_df(table)
            table_csv = df.to_csv(index=False)

        return prompt.format(table_csv)
    

    def table_to_csv(self, table):
        df = self.table_to_df(table)
        table_csv = df.to_csv(index=False)
        return table_csv

    def table_to_df(self, table):
        table_el = self._get_main_table_html(table)
        table_html = table_el.render()
        df = pd.read_html(table_html)[0]
        return df

    def table_to_html(self, table):
        if table.props:
            meta_trs = []
            for key, value in table.props.items():
                meta_trs.append([h("th")(key), h("td")(value)])

            meta_tbodies = [h("tr")(tds) for tds in meta_trs]
            meta_tbody_el = h("tbody")(meta_tbodies)
            meta_table_el = h("table", klass="table table-sm caption-top meta-table")(h("caption")("properties"),meta_tbody_el)
        else: 
            meta_table_el = None

        table_el = self._get_main_table_html(table)
        area_el = h("div")(meta_table_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(
            lxml.html.fromstring(html), encoding="unicode", pretty_print=True
        )


    def _get_main_table_html(self, table):
        trs = []
        for row in table.cells:
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

        return table_el


    


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
        except (AssertionError, ValueError, TypeError) as e:
            # max_examples is set higher than the total number of examples in the dataset
            dataset = datasets.load_dataset(self.hf_id, name=self.hf_extra_config, split=hf_split)
        
        self.dataset_info = dataset.info.__dict__
        self.data[split] = dataset

    def get_info(self):
        info = {key: self.dataset_info[key] for key in ["citation", "description", "homepage"]}
        info["name"] = self.name

        return info