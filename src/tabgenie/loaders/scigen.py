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

    def prepare_table(self, entry):
        t = Table()
        caption = entry["table_caption"]
        t.props["reference"] = caption.replace("[CONTINUE]", "\n")
        t.props["title"] = entry["paper"]
        t.props["text"] = (entry.get("text") or "").replace("[CONTINUE]", "\n")
        t.props["paper_id"] = entry.get("paper_id")

        for col in ast.literal_eval(entry["table_column_names"]):
            c = Cell()
            c.value = self.normalize(col)
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
