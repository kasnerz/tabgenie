#!/usr/bin/env python3
import json
import os

from .data import Cell, Table, TabularDataset


class NumericNLG(TabularDataset):
    """
    The NumericNLG dataset: https://github.com/titech-nlp/numeric-nlg
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_table(self, split, index):
        entry = self.data[split][index]

        t = Table()
        t.ref = entry["ref"]
        t.title = entry["title"]

        for i in range(entry["column_header_level"]):
            c = Cell("")
            c.colspan = int(entry["row_header_level"])
            c.is_col_header = True
            t.add_cell(c)

            for header_set in entry["column_headers"]:
                try:
                    col = header_set[i]
                except IndexError:
                    col = ""
                c = Cell(col)
                # c.colspan = len(col)
                c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        for i, row in enumerate(entry["contents"]):
            row_headers = entry["row_headers"][i]
            
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

    def load(self, split, max_examples=None):
        filename = split if split != "dev" else "val"
        # refs = {}
        # with open(os.path.join(self.path, f"table_desc_{filename}.json")) as f:
        #     j = json.load(f)

        # for example in j:
        #     refs[example["table_id"]] = example["description"]

        with open(os.path.join(self.path, f"table_{filename}.json")) as f:
            j = json.load(f)

        for i, example in enumerate(j):
            if max_examples is not None and i > max_examples:
                break
            
            self.data[split].append(
                {
                    "contents": example["contents"],
                    "row_headers": example["row_headers"],
                    "column_headers": example["column_headers"],
                    "row_header_level": example["row_header_level"],
                    "column_header_level": example["column_header_level"],
                    # "ref": refs[example["table_id"]],
                    "ref": example["caption"],
                    "title": example["table_name"],
                }
            )
