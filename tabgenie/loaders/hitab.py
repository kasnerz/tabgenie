#!/usr/bin/env python3
import re
import ast

from ..structs.data import Cell, Table, HFTabularDataset


class HiTab(HFTabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/hitab"
        self.name = "HiTab"

    @staticmethod
    def _get_linked_cells(linked_cells):
        # the design of the `linked_cells` dictionary is very unintuitive
        # extract the highlighted cells the quick and dirty way
        s = str(linked_cells)
        cells = [eval(x) for x in re.findall(r"\(\d+, \d+\)", s)]
        return cells

    def prepare_table(self, entry):
        t = Table()
        t.props["reference"] = entry["sub_sentence"]
        content = ast.literal_eval(entry["table_content"])
        linked_cells = self._get_linked_cells(ast.literal_eval(entry["linked_cells"]))

        t.props["title"] = content.get("title")
        t.props["table_id"] = entry.get("table_id")
        t.props["table_source"] = entry.get("table_source")

        for i, row in enumerate(content["texts"]):
            for j, col in enumerate(row):
                c = Cell()
                c.value = col
                c.is_col_header = i < content["top_header_rows_num"] - 1
                c.is_row_header = j < content["left_header_columns_num"]
                c.is_highlighted = (i, j) in linked_cells
                t.add_cell(c)
            t.save_row()

        for r in content["merged_regions"]:
            for i in range(r["first_row"], r["last_row"] + 1):
                for j in range(r["first_column"], r["last_column"] + 1):
                    cell = t.get_cell(i, j)
                    if cell is None:  # out of bounds
                        continue

                    if i == r["first_row"] and j == r["first_column"]:
                        cell.rowspan = r["last_row"] - r["first_row"] + 1
                        cell.colspan = r["last_column"] - r["first_column"] + 1
                    else:
                        cell.is_dummy = True
                        c = t.get_cell(r["first_row"], r["first_column"])
                        cell.main_cell = (r["first_row"], r["first_column"])
                        cell.is_col_header = c.is_col_header
                        cell.is_row_header = c.is_row_header
                        cell.is_highlighted = c.is_highlighted
                        cell.value = c.value

        return t
