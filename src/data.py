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
from .utils.text import normalize

from tinyhtml import h

logger = logging.getLogger(__name__)

def get_dataset_class_by_name(name):
    """
    A helper function which allows to use the class attribute `name` of a Dataset 
    (sub)class as a command-line parameter for loading the dataset.
    """
    try:
        # case-insensitive
        available_classes = {o.name.lower() : o for o in globals().values() 
                                if type(o)==type(Dataset) and hasattr(o, "name")}
        return available_classes[name.lower()]
    except AttributeError:
        logger.error(f"Unknown dataset: '{args.dataset}'. Please create \
            a class with an attribute name='{args.dataset}' in 'data.py'. \
            Available classes: {available_classes}")
        return None

class DataEntry:
    """ 
    An entry in the dataset 
    """
    def __init__(self, data, refs, data_type):
        self.data = data
        self.refs = refs
        self.data_type = data_type

    def __repr__(self):
        return str(self.__dict__)


class Dataset:
    """
    Base class for the datasets
    """
    def __init__(self, path):
        self.splits =  ["train", "dev", "test"]
        self.data = {split: [] for split in self.splits}
        self.path = path

    def load(self):
        """
        Load the dataset. Path can be specified for loading from a directory
        or omitted if the dataset is loaded from HF.
        """
        raise NotImplementedError

    def get_table_html(self, split, index):
        raise NotImplementedError

    def get_reference(self, split, index):
        raise NotImplementedError

    def has_split(self, split):
        return bool(self.data[split])


class SciGen(Dataset):
    name = "scigen"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tables = {}


    def get_reference(self, split, index):
        entry = self.data[split][index]
        caption = entry["table_caption"]
        caption = caption.replace("[CONTINUE]", "\n")

        return caption

    def normalize(self, s):
        # just ignore inline tags and italics
        s = re.sub(r"</*(italic|bold)>", "", s)
        s = re.sub(r"\[ITALIC\]", "", s)

        if "[BOLD]" in s:
            s = s.replace("[BOLD]", "")
            return h("b")(s)

        if "[EMPTY]" in s:
            return ""

        return s
        

    def get_table_html(self, split, index):
        entry = self.data[split][index]

        headers = []
        headers.append(h("p")(h("h5")(entry["paper"])))
        header_el = h("div")(headers)

        trs = []

        ths = []
        for j, col in enumerate(entry["table_column_names"]):
            th_el =  h("th")(self.normalize(col))
            ths.append(th_el)
        
        trs.append(ths)

        for i, row in enumerate(entry["table_content_values"]):
            tds = []
            for j, col in enumerate(row):
                td_el = h("td")(self.normalize(col))
                tds.append(td_el)
            trs.append(tds)

        tbodies = [h("tr")(tds) for tds in trs]
        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)


    def load(self, split):
        data_dir = "development" if split == "dev" else split

        if split in ["train", "dev"]:
            file_path = os.path.join(self.path, data_dir, "medium", f"{split}.json")
        else:
            # there is also "test-Other.json", should be looked into
            file_path = os.path.join(self.path, data_dir, f"test-CL.json")

        with open(file_path) as f:
            j = json.load(f)
            self.data[split] = list(j.values())


class HiTab(Dataset):
    name = "hitab"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tables = {}

    def _get_linked_cells(self, linked_cells):
        # the design of the `linked_cells` dictionary is very unintuitive
        # extract the highlighted cells the quick and dirty way
        s = str(linked_cells)
        cells = [eval(x) for x in re.findall(r"\(\d+, \d+\)", s)]
        return cells

    def get_reference(self, split, index):
        entry = self.data[split][index]
        return entry["sub_sentence"]

    def get_table_html(self, split, index):
        def is_highlighted(i, j):
            return (i,j) in linked_cells

        entry = self.data[split][index]
        table = self.tables.get(entry["table_id"])

        if not table:
            logger.warning("Table not found")
            return ""

        linked_cells = self._get_linked_cells(entry["linked_cells"])

        headers = []
        headers.append(h("p")(h("h5")(table["title"])))
        header_el = h("div")(headers)

        trs = []
        for i, row in enumerate(table["texts"]):
            tds = []
            for j, col in enumerate(row):
                if i < table["top_header_rows_num"]-1 or j < table["left_header_columns_num"]:
                    td_el = h("th")(col)
                else:
                    td_el = h("td")(col)

                if is_highlighted(i,j):
                    td_el.tag.attrs["class"] = "table-active"

                tds.append(td_el)
            trs.append(tds)

        for r in table["merged_regions"]:
            for i in range(r["first_row"], r["last_row"]+1):
                for j in range(r["first_column"], r["last_column"]+1):
                    if i == r["first_row"] and j == r["first_column"]:
                        trs[i][j].tag.attrs["rowspan"] = r["last_row"]-r["first_row"]+1
                        trs[i][j].tag.attrs["colspan"] = r["last_column"]-r["first_column"]+1
                    else:
                        trs[i][j] = None

        tbodies = [h("tr")(tds) for tds in trs]
        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)


    def load(self, split):
        for filename in glob.glob(os.path.join(self.path, "tables", "raw", "*.json")):
            with open(filename) as f:
                j = json.load(f)
                table_name = os.path.basename(filename).rstrip(".json")
                self.tables[table_name] = j

        with open(os.path.join(self.path, f"{split}_samples.jsonl")) as f:
            for line in f.readlines():
                j = json.loads(line)
                self.data[split].append(j)


class ToTTo(Dataset):
    """
    The ToTTo dataset: https://github.com/google-research-datasets/ToTTo
    Contains tables from English Wikipedia with highlighted cells 
    and the crowdsourced verbalizations of these cells.
    """
    name="totto"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_reference(self, split, index):
        table_raw = self.data[split][index]
        return table_raw["target"]


    def get_table_html(self, split, index):
        def is_highlighted(i, j):
            return [i,j] in table_raw["highlighted_cells"]

        table_raw = self.data[split][index]
        headers = []

        if table_raw["table_webpage_url"]:
            headers.append(h("p")(h("a", href=table_raw["table_webpage_url"])(h("h3")(table_raw["table_page_title"]))))
        else:
            headers.append(h("p")(h("h5")(table_raw["table_page_title"])))

        if table_raw.get("table_section_text"):
            headers.append(h("p")(h("b")(table_raw["table_section_text"])))

        if table_raw.get("table_section_title"):
            headers.append(h("p")(h("b")(table_raw["table_section_title"])))

        header_el = h("div")(headers)

        theaders = []
        thead_el = None
        tbodies = []

        for i, row in enumerate(table_raw["table"]):
            if i==0 and all([x["is_header"] for x in row]):
                for j, x in enumerate(row):
                    th_el = h("th", scope="col", colspan=x["column_span"], rowspan=x["row_span"])(x["value"])
                    if is_highlighted(i,j):
                        td_el.tag.attrs["class"] = "table-active"
                    theaders.append(th_el)
                thead_el = h("thead")(theaders)
            else:
                tds = []
                for j, x in enumerate(row):
                    if x["is_header"]:
                        td_el = h("th", scope="row", colspan=x["column_span"], rowspan=x["row_span"])(x["value"])
                    else:
                        td_el = h("td", colspan=x["column_span"], rowspan=x["row_span"])(x["value"])
                    if is_highlighted(i,j):
                        td_el.tag.attrs["class"] = "table-active"
                    tds.append(td_el)
                tr_el = h("tr")(tds)
                tbodies.append(tr_el)

        tbody_el = h("tbody")(tbodies)

        # footers = []
        
        # footer_el = h("div")(footers)
        
        table_el = h("table", klass="table table-sm table-bordered")(thead_el, tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)



    def load(self, split):
        dataset = load_dataset("gem", "totto")
    
        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data


class WebNLG(Dataset):
    """
    The WebNLG dataset: https://huggingface.co/datasets/web_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """
    name="webnlg"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_reference(self, split, index):
        table_raw = self.data[split][index]
        return table_raw["target"]


    def get_table_html(self, split, index):
        example = self.data[split][index]
        theaders = [
            h("th", scope="col")("subject"),
            h("th", scope="col")("predicate"),
            h("th", scope="col")("object"),
        ]
        thead_el = None
        thead_el = h("thead")(theaders)
        tbodies = []

        for triple in example["input"]:
            tds = []
            elems = triple.split("|")
            for el in elems:
                el = normalize(el, remove_parentheses=False)
                td_el = h("td")(el)
                tds.append(td_el)

            tr_el = h("tr")(tds)
            tbodies.append(tr_el)

        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(thead_el, tbody_el)
        area_el = h("div")(table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)


    def load(self, split):
        dataset = load_dataset("gem", "web_nlg_en")
    
        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data


class LogicNLG(Dataset):
    """
    The LogicNLG dataset: https://github.com/wenhuchen/LogicNLG
    Contains tables from English Wikipedia and crowdsourced verbalizations with logical inferences.
    """
    name="logicnlg"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}

    def get_reference(self, split, index):
        table = self.data[split][index]
        return table["ref"]


    def get_table_html(self, split, index):
        def is_highlighted(i):
            return j in table["linked_columns"]

        table = self.data[split][index]
        headers = []
        headers.append(h("p")(h("h5")(table["title"])))
        header_el = h("div")(headers)

        theaders = []
        thead_el = None
        tbodies = []

        for i, row in enumerate(table["table"]):
            if i==0:
                for j, x in enumerate(row):
                    th_el = h("th", scope="col")(x)
                    if is_highlighted(i):
                        th_el.tag.attrs["class"] = "table-active"
                    theaders.append(th_el)
                thead_el = h("thead")(theaders)
            else:
                tds = []
                for j, x in enumerate(row):
                    td_el = h("td")(x)
                    if is_highlighted(i):
                        td_el.tag.attrs["class"] = "table-active"
                    tds.append(td_el)
                tr_el = h("tr")(tds)
                tbodies.append(tr_el)

        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(thead_el, tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)


    def load(self, split):
        filename = split if split != "dev" else "val"

        with open(os.path.join(self.path, f"{filename}_lm.json")) as f:
            j = json.load(f)
        
        for table_id, examples in j.items():
            table = []
            with open(os.path.join(self.path, "all_csv", table_id)) as f:
                for line in f.readlines():
                    table.append(line.rstrip("\n").split("#"))

            for example in examples:
                self.data[split].append({
                    "table" : table,
                    "ref" : example[0],
                    "linked_columns" : example[1],
                    "title" : example[2],
                    "template" : example[3]
                })