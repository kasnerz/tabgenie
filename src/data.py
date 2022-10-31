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

class Cell:
    """ 
    Table cell
    """
    def __init__(self):
        self.idx = None
        self.value = None
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


class Dataset:
    """
    Base class for the datasets
    """
    def __init__(self, path):
        self.splits =  ["train", "dev", "test"]
        self.data = {split: [] for split in self.splits}
        self.tables = {split: {} for split in self.splits}
        self.path = path

    def load(self):
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
                td_el = h(eltype, colspan=c.colspan, rowspan=c.rowspan, cell_idx=c.idx)(c.value)

                if c.is_highlighted:
                    td_el.tag.attrs["class"] = "table-active"

                tds.append(td_el)
            trs.append(tds)

        tbodies = [h("tr")(tds) for tds in trs]
        tbody_el = h("tbody")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered")(tbody_el)
        area_el = h("div")(header_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)



class SciGen(Dataset):
    name = "scigen"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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

    def prepare_table(self, split, index):
        t = Table()
        entry = self.data[split][index]

        caption = entry["table_caption"]
        t.ref = caption.replace("[CONTINUE]", "\n")
        t.title = entry["paper"]

        for col in entry["table_column_names"]:
            c = Cell()
            c.value = self.normalize(col)
            c.is_col_header = True
            t.add_cell(c)
        
        t.save_row()

        for row in entry["table_content_values"]:
            for col in row:
                c = Cell()
                c.value = self.normalize(col)
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t


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
        self.table_content = {}

    def _get_linked_cells(self, linked_cells):
        # the design of the `linked_cells` dictionary is very unintuitive
        # extract the highlighted cells the quick and dirty way
        s = str(linked_cells)
        cells = [eval(x) for x in re.findall(r"\(\d+, \d+\)", s)]
        return cells

    def prepare_table(self, split, index):
        t = Table()
        entry = self.data[split][index]
        t.ref = entry["sub_sentence"]
        content = self.table_content.get(entry["table_id"])
        linked_cells = self._get_linked_cells(entry["linked_cells"])

        t.title = content["title"]
            
        for i, row in enumerate(content["texts"]):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                c.is_col_header = i < content["top_header_rows_num"]-1
                c.is_row_header =  j < content["left_header_columns_num"]
                c.is_highlighted = (i,j) in linked_cells
                t.add_cell(c)
            t.save_row()

        for r in content["merged_regions"]:
            for i in range(r["first_row"], r["last_row"]+1):
                for j in range(r["first_column"], r["last_column"]+1):
                    if i == r["first_row"] and j == r["first_column"]:
                        t.get_cell(i,j).rowspan = r["last_row"]-r["first_row"]+1
                        t.get_cell(i,j).colspan = r["last_column"]-r["first_column"]+1
                    else:
                        t.get_cell(i,j).is_dummy = True

        self.tables[split][index] = t
        return t


    def load(self, split):
        for filename in glob.glob(os.path.join(self.path, "tables", "raw", "*.json")):
            with open(filename) as f:
                j = json.load(f)
                table_name = os.path.basename(filename).rstrip(".json")
                self.table_content[table_name] = j

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


    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]
        t.url = entry["table_webpage_url"]
        t.title = entry["table_page_title"]

        if entry.get("table_section_text"):
            t.extra_headers.append(entry.get("table_section_text"))

        if entry.get("table_section_title"):
            t.extra_headers.append(entry.get("table_section_title"))

        for i, row in enumerate(entry["table"]):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x["value"]
                c.colspan = x["column_span"]
                c.rowspan = x["row_span"]
                c.is_highlighted = [i,j] in entry["highlighted_cells"]
                c.is_col_header = x["is_header"] and i == 0
                c.is_row_header = x["is_header"] and i != 0
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t


    def load(self, split):
        dataset = load_dataset("gem", "totto")
    
        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data


class WebNLG(Dataset):
    """
    The WebNLG dataset: https://huggingface.co/datasets/GEM/web_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """
    name="webnlg"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]

        for val in ["subject", "predicate", "object"]:
            c = Cell()
            c.value = val
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()

        for triple in entry["input"]:
            elems = triple.split("|")
            for el in elems:
                c = Cell()
                c.value = normalize(el, remove_parentheses=False)
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t

    def load(self, split):
        dataset = load_dataset("gem", "web_nlg_en")
    
        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data


class E2E(Dataset):
    """
    The Cleaned E2E dataset: https://huggingface.co/datasets/GEM/e2e_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """
    name="e2e"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]
        mrs = entry["meaning_representation"].split(", ")

        for mr in mrs:
            key = mr.split("[")[0]
            c = Cell()
            c.value = key
            c.is_col_header = True
            t.add_cell(c)
        t.save_row()

        for mr in mrs:
            value = mr.split("[")[1][:-1]
            c = Cell()
            c.value = value
            t.add_cell(c)
        t.save_row()
            

        self.tables[split][index] = t
        return t

    def load(self, split):
        dataset = load_dataset("gem", "e2e_nlg")
    
        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data



class LogicNLG(Dataset):
    """
    The LogicNLG dataset: https://github.com/wenhuchen/LogicNLG
    Contains tables from the repurposed TabFact dataset (English Wikipedia).
    The references are the entailed statements containing logical inferences.
    """
    name="logicnlg"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}


    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["ref"]
        t.title = entry["title"]

        for i, row in enumerate(entry["table"]):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                c.is_highlighted = j in entry["linked_columns"]
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t


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


class Logic2Text(Dataset):
    """
    The Logic2Text dataset: https://github.com/czyssrs/Logic2Text
    Contains tables + explicit logical forms from which a utterance should be generated.
    """
    name="logic2text"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_table(self, split, index):
        def is_highlighted(i, j):
            # TODO: add other cases in the dataset such as "col_superlative" and "row_superlative" or subsets
            if all(x in entry["annotation"] for x in ["row_1", "row_2", "col", "col_other"]):
                return (
                    str(i+1) == entry["annotation"]["row_1"]
                    or str(i+1) == entry["annotation"]["row_Ě"]
                ) and (
                    str(j+1) == entry["annotation"]["col"]
                    or str(j+1) == entry["annotation"]["col_other"]
                )
            elif all(x in entry["annotation"] for x in ["row", "col", "col_other"]):
                return str(i+1) == entry["annotation"]["row"] and (
                    str(j+1) == entry["annotation"]["col"]
                    or str(j+1) == entry["annotation"]["col_other"]
                )
            elif "col" in entry["annotation"]:
                return str(j+1) == entry["annotation"]["col"]
            else:
                return False

        entry = self.data[split][index]
        t = Table()
        t.ref = entry["sent"]
        t.url = entry["url"]
        t.title = entry["topic"]
        t.extra_headers.append(entry["logic_str"])

        for j, x in enumerate(entry["table_header"]):
            c = Cell()
            c.value = x
            c.is_highlighted = is_highlighted(0, j)
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()
        for i, row in enumerate(entry["table_cont"]):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                c.is_highlighted = is_highlighted(i, j)
                t.add_cell(c)

            t.save_row()

        self.tables[split][index] = t
        return t


    def load(self, split):
        filename = split if split != "dev" else "valid"

        with open(os.path.join(self.path, f"{filename}.json")) as f:
            self.data[split] = json.load(f)


class ChartToTextS(Dataset):
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

        with open(os.path.join(self.path, "dataset_split", f"{mapping_file}_index_mapping.csv")) as f:
            next(f)
            for line in f:
                subdir = "." if line.startswith("two_col") else "multiColumn"
                filename = line.split("-")[1].split(".")[0]
                
                with open(os.path.join(self.path, subdir, "data", filename + ".csv")) as g:
                    content = []
                    reader = csv.reader(g, delimiter=',', quotechar='"')
                    for row in reader:
                        content.append(row)

                with open(os.path.join(self.path, subdir, "captions", filename + ".txt")) as g:
                    ref = g.read().rstrip("\n")

                with open(os.path.join(self.path, subdir, "titles", filename + ".txt")) as g:
                    title = g.read().rstrip("\n")

                self.data[split].append({
                    "content" : content,
                    "ref" : ref,
                    "title" : title
                })