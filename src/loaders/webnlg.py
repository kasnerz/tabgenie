#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, TabularDataset
from ..utils.text import normalize


class WebNLG(TabularDataset):
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