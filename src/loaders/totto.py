#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, TabularDataset


class ToTTo(TabularDataset):
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