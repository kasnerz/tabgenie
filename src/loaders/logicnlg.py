#!/usr/bin/env python3
import json
import os

from .data import Cell, Table, TabularDataset


class LogicNLG(TabularDataset):
    """
    The LogicNLG dataset: https://github.com/wenhuchen/LogicNLG
    Contains tables from the repurposed TabFact dataset (English Wikipedia).
    The references are the entailed statements containing logical inferences.
    """

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

    def load(self, split, max_examples=None):
        filename = split if split != "dev" else "val"

        with open(os.path.join(self.path, f"{filename}_lm.json")) as f:
            j = json.load(f)

        for table_id, examples in j.items():
            table = []
            with open(os.path.join(self.path, "all_csv", table_id)) as f:
                for line in f.readlines():
                    table.append(line.rstrip("\n").split("#"))

            for example in examples:
                if max_examples is not None:
                    break

                self.data[split].append(
                    {
                        "table": table,
                        "ref": example[0],
                        "linked_columns": example[1],
                        "title": example[2],
                        "template": example[3],
                    }
                )
