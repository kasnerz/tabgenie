#!/usr/bin/env python3
import json
import os
import ast
from .data import Cell, Table, HFTabularDataset


class LogicNLG(HFTabularDataset):
    """
    The LogicNLG dataset: https://github.com/wenhuchen/LogicNLG
    Contains tables from the repurposed TabFact dataset (English Wikipedia).
    The references are the entailed statements containing logical inferences.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}
        self.hf_id = "kasnerz/logicnlg"
        self.name = "LogicNLG"

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()


        t.ref = entry["ref"]
        t.title = entry["title"]

        for i, row in enumerate(ast.literal_eval(entry["table"])):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                c.is_highlighted = j in ast.literal_eval(entry["linked_columns"])
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t
