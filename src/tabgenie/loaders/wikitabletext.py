#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset
import ast


class WikiTableText(HFTabularDataset):
    """
    The WikiTableText dataset: https://github.com/msra-nlc/Table2Text
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/wikitabletext"
        self.name = "WikiTableText"

    def prepare_table(self, split, table_idx):
        entry = self.data[split][table_idx]

        t = Table()
        t.props["reference"] = entry["reference"]
        t.props["row_number"] = entry["row_number"]

        headers = ast.literal_eval(entry["headers"])
        content = ast.literal_eval(entry["content"])

        for key, val in zip(headers, content):
            c = Cell(key)
            c.is_row_header = True
            t.add_cell(c)

            c = Cell(val)
            t.add_cell(c)
            t.save_row()

        return t
