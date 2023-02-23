#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset


class ToTTo(HFTabularDataset):
    """
    The ToTTo dataset: https://github.com/google-research-datasets/ToTTo
    Contains tables from English Wikipedia with highlighted cells
    and the crowdsourced verbalizations of these cells.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/totto"
        self.name = "ToTTo"
        self.extra_info = {"license": "CC BY-SA 3.0"}

    def prepare_table(self, entry):
        t = Table()
        t.props["reference"] = entry["target"]

        t.props["title"] = entry["table_page_title"]
        if entry.get("table_section_text"):
            t.props["table_section_text"] = entry["table_section_text"]

        if entry.get("table_section_title"):
            t.props["table_section_title"] = entry["table_section_title"]

        t.props["references"] = str(entry["references"])
        t.props["linearized_input"] = entry["linearized_input"]
        t.props["overlap_subset"] = entry["overlap_subset"]
        t.props["url"] = entry["table_webpage_url"]

        for i, row in enumerate(entry["table"]):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x["value"]
                c.colspan = x["column_span"]
                c.rowspan = x["row_span"]
                c.is_highlighted = [i, j] in entry["highlighted_cells"]
                c.is_col_header = x["is_header"] and i == 0
                c.is_row_header = x["is_header"] and i != 0
                t.add_cell(c)
            t.save_row()

        return t
