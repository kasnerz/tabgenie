#!/usr/bin/env python3
import ast

from ..structs.data import Cell, Table, HFTabularDataset


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

    def prepare_table(self, split, table_idx):
        entry = self.data[split][table_idx]
        t = Table()

        t.set_generated_output("reference", entry["ref"])
        t.props["title"] = entry["title"]
        t.props["table_id"] = entry["table_id"]
        t.props["template"] = entry["template"]
        t.props["linked_columns"] = entry["linked_columns"]

        for i, row in enumerate(ast.literal_eval(entry["table"])):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                # c.is_highlighted = j in ast.literal_eval(entry["linked_columns"])
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        return t
