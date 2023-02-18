#!/usr/bin/env python3
import ast

from ..structs.data import Cell, Table, HFTabularDataset


class ChartToTextS(HFTabularDataset):
    """
    The "Statista" subset of the Chart-To-Text dataset: https://github.com/vis-nlp/Chart-to-text/tree/main/statista_dataset/dataset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.table_content = {}
        self.hf_id = "kasnerz/charttotext-s"
        self.name = "Chart-to-Text (Statista subset)"

    def prepare_table(self, entry):
        t = Table()
        t.props["reference"] = entry["ref"]
        t.props["title"] = entry["title"]

        for i, row in enumerate(ast.literal_eval(entry["content"])):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                if i == 0:
                    c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        return t
