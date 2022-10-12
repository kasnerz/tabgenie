#!/usr/bin/env python3

import json
import csv
import os
import logging
import re
import random
import datasets
import lxml.etree
import lxml.html

from collections import defaultdict, namedtuple
from datasets import load_dataset
from .utils.text import normalize

from tinyhtml import html, h, frag, raw

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
    def __init__(self):
        self.data = {split: [] for split in ["train", "dev", "test"]}

    def load(self, splits, path=None):
        """
        Load the dataset. Path can be specified for loading from a directory
        or omitted if the dataset is loaded from HF.
        """
        raise NotImplementedError


class ToTTo(Dataset):
    """
    The ToTTo dataset: https://github.com/google-research-datasets/ToTTo
    Contains tables from English Wikipedia with highlighted cells 
    and the crowdsourced verbalizations of these cells.
    """
    name="totto"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_raw = {}


    def get_table_html(self, split, index):

        def is_highlighted(i, j):
            return [i,j] in table_raw["highlighted_cells"]

        table_raw = self.data_raw[split][index]
        headers = []

        if table_raw["table_webpage_url"]:
            headers.append(h("p")(h("a", href=table_raw["table_webpage_url"])(h("h3")(table_raw["table_page_title"]))))
        else:
            headers.append(h("p")(h("h3")(table_raw["table_page_title"])))

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
                    th_el = h("th", scope="col", colspan=x["column_span"])(x["value"])
                    if is_highlighted(i,j):
                        td_el.tag.attrs["class"] = "table-active"
                    theaders.append(th_el)
                thead_el = h("thead")(theaders)
            else:
                tds = []
                for j, x in enumerate(row):
                    if x["is_header"]:
                        td_el = h("th", scope="row", colspan=x["column_span"])(x["value"])
                    else:
                        td_el = h("td", colspan=x["column_span"])(x["value"])
                    if is_highlighted(i,j):
                        td_el.tag.attrs["class"] = "table-active"
                    tds.append(td_el)
                tr_el = h("tr")(tds)
                tbodies.append(tr_el)

        tbody_el = h("tbody")(tbodies)

        footers = []
        footers.append(h("p")(table_raw["target"]))
        footer_el = h("div")(footers)
        
        table_el = h("table", klass="table table-hover table-sm table-bordered")(thead_el, tbody_el)
        area_el = h("div")(header_el, table_el, footer_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding='unicode', pretty_print=True)



    def load(self, splits, path=None):
        dataset = load_dataset("gem", "totto")
    
        for split in splits:
            data = dataset[split if split != "dev" else "validation"]
            self.data_raw[split] = data
