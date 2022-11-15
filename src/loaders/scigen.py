#!/usr/bin/env python3
import json
import os
import re
from .data import Cell, Table, TabularDataset
from tinyhtml import h


class SciGen(TabularDataset):
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
