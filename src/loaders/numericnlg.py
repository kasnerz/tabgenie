#!/usr/bin/env python3
import json
import os
import ast
from .data import Cell, Table, TabularDataset, HFTabularDataset


class NumericNLG(HFTabularDataset):
    """
    The NumericNLG dataset: https://github.com/titech-nlp/numeric-nlg
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/numericnlg"
        self.name = "NumericNLG"

    def prepare_table(self, split, index):
        entry = self.data[split][index]

        t = Table()
        t.ref = entry["caption"]
        t.title = entry["table_name"]

        for i in range(int(entry["column_header_level"])):
            c = Cell("")
            c.colspan = int(entry["row_header_level"])
            c.is_col_header = True
            t.add_cell(c)

            for header_set in ast.literal_eval(entry["column_headers"]):
                try:
                    col = header_set[i]
                except IndexError:
                    col = ""
                c = Cell(col)
                # c.colspan = len(col)
                c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        for i, row in enumerate(ast.literal_eval(entry["contents"])):
            row_headers = ast.literal_eval(entry["row_headers"])[i]
            
            for j, header in enumerate(row_headers):
                c = Cell(header)
                c.is_row_header = True
                t.add_cell(c)

            for j, x in enumerate(row):
                c = Cell(x)
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t
