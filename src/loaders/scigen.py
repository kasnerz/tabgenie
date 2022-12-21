#!/usr/bin/env python3
import json
import os
import re
import ast
from .data import Cell, Table, TabularDataset, HFTabularDataset
from tinyhtml import h

class SciGen(HFTabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/scigen"
        self.name = "SciGen"

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
        
        t.props["title"] = entry["paper"]

        for col in ast.literal_eval(entry["table_column_names"]):
            c = Cell()
            c.value = self.normalize(col)
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()

        for row in ast.literal_eval( entry["table_content_values"]):
            for col in row:
                c = Cell()
                c.value = self.normalize(col)
                t.add_cell(c)
            t.save_row()

        return t