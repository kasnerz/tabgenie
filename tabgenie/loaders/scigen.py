#!/usr/bin/env python3
import re
import ast

from tinyhtml import h

from ..structs.data import Cell, Table, HFTabularDataset


class SciGen(HFTabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/scigen"
        self.name = "SciGen"

    def normalize(self, s, is_header=False):
        # just ignore inline tags and italics
        s = re.sub(r"</*(italic|bold)>", "", s)
        s = re.sub(r"\[ITALIC\]", "", s)

        if "[BOLD]" in s:
            s = s.replace("[BOLD]", "")
            return s if is_header else h("b")(s)

        if "[EMPTY]" in s:
            return ""

        return s

    def prepare_table(self, entry):
        t = Table()
        t.props["references"] = [(entry.get("text") or "").replace("[CONTINUE]", "\n")]
        t.props["title"] = entry["table_caption"].replace("[CONTINUE]", "\n")
        t.props["paper"] = entry["paper"]
        t.props["paper_id"] = entry.get("paper_id")

        for col in ast.literal_eval(entry["table_column_names"]):
            c = Cell()
            c.value = self.normalize(col, is_header=True)
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()

        for row in ast.literal_eval(entry["table_content_values"]):
            for col in row:
                c = Cell()
                c.value = self.normalize(col)
                t.add_cell(c)
            t.save_row()

        return t
