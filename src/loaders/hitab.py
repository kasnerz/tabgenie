#!/usr/bin/env python3
import json
import os
import re
import glob
import ast
from .data import Cell, Table, TabularDataset, HFTabularDataset


class HiTab(HFTabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = 'kasnerz/hitab'
        self.name = "HiTab"

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
        content = ast.literal_eval(entry["table_content"])
        linked_cells = self._get_linked_cells(ast.literal_eval(entry["linked_cells"]))

        t.props["title"] = content["title"]

        for i, row in enumerate(content["texts"]):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                c.is_col_header = i < content["top_header_rows_num"] - 1
                c.is_row_header = j < content["left_header_columns_num"]
                c.is_highlighted = (i, j) in linked_cells
                t.add_cell(c)
            t.save_row()

        for r in content["merged_regions"]:
            for i in range(r["first_row"], r["last_row"] + 1):
                for j in range(r["first_column"], r["last_column"] + 1):
                    if i == r["first_row"] and j == r["first_column"]:
                        t.get_cell(i, j).rowspan = r["last_row"] - r["first_row"] + 1
                        t.get_cell(i, j).colspan = (
                            r["last_column"] - r["first_column"] + 1
                        )
                    else:
                        t.get_cell(i, j).is_dummy = True

        return t

   