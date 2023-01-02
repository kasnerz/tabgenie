#!/usr/bin/env python3
import json
import os
import ast
from .data import Cell, Table, HFTabularDataset


class Logic2Text(HFTabularDataset):
    """
    The Logic2Text dataset: https://github.com/czyssrs/Logic2Text
    Contains tables + explicit logical forms from which a utterance should be generated.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/logic2text"
        self.name = "Logic2Text"

    def prepare_table(self, split, index):
        def is_highlighted(i, j):
            # TODO: add other cases in the dataset such as "col_superlative" and "row_superlative" or subsets
            if all(
                x in entry["annotation"] for x in ["row_1", "row_2", "col", "col_other"]
            ):
                return (
                    str(i + 1) == entry["annotation"]["row_1"]
                    or str(i + 1) == entry["annotation"]["row_2"]
                ) and (
                    str(j + 1) == entry["annotation"]["col"]
                    or str(j + 1) == entry["annotation"]["col_other"]
                )
            elif all(x in entry["annotation"] for x in ["row", "col", "col_other"]):
                return str(i + 1) == entry["annotation"]["row"] and (
                    str(j + 1) == entry["annotation"]["col"]
                    or str(j + 1) == entry["annotation"]["col_other"]
                )
            elif "col" in entry["annotation"]:
                return str(j + 1) == entry["annotation"]["col"]
            else:
                return False

        entry = self.data[split][index]
        entry["annotation"] = ast.literal_eval(entry["annotation"])
        t = Table()
        t.set_generated_output("reference", entry["sent"])

        t.props["title"] = entry["topic"]
        t.props["url"] = entry["url"]
        t.props["logic_str"] = entry["logic_str"]

        for j, x in enumerate(ast.literal_eval(entry["table_header"])):
            c = Cell()
            c.value = x
            c.is_highlighted = is_highlighted(0, j)
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()
        for i, row in enumerate(ast.literal_eval(entry["table_cont"])):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                c.is_highlighted = is_highlighted(i, j)
                t.add_cell(c)

            t.save_row()

        return t
