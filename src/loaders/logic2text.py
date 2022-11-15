#!/usr/bin/env python3
import json
import os

from .data import Cell, Table, TabularDataset

class Logic2Text(TabularDataset):
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
                    or str(i+1) == entry["annotation"]["row_2"]
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