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
        self.hf_id = 'GEM/totto'
        self.name = "ToTTo"

    def prepare_table(self, split, table_idx):
        entry = self.data[split][table_idx]
        t = Table()
        t.props["reference"] = entry["target"]

        t.props["title"] = entry["table_page_title"]

        if entry.get("table_section_text"):
            t.props["table_section_text"] = entry["table_section_text"]

        if entry.get("table_section_title"):
            t.props["table_section_title"] = entry["table_section_title"]
        
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

    def table_to_linear(self, table, cell_ids=None):
        if cell_ids:
            cells = [table.get_cell_by_id(int(idx)) for idx in cell_ids]
        else:
            cells = table.get_flat_cells(highlighted_only=True)

        gen_input = []

        for key, value in table.props.items():
            gen_input.append(f"[{key}] {value}")

        for c in cells:
            gen_input.append("[cell] " + c.value)

        return " ".join(gen_input)