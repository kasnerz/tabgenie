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

    def get_task_definition(self):
        return "Give a description of the selected table cells."

    @staticmethod
    def _write_cells(table_obj, entry):
        taken_cells = set()

        for i, row in enumerate(entry["table"]):
            col_num = 0
            while (i, col_num) in taken_cells:
                c = Cell()
                c.is_dummy = True
                table_obj.add_cell(c)
                col_num += 1

            for j, x in enumerate(row):
                while (i, col_num) in taken_cells:
                    c = Cell()
                    c.is_dummy = True
                    table_obj.add_cell(c)
                    col_num += 1

                c = Cell()
                c.value = x["value"]
                c.colspan = x["column_span"]
                c.rowspan = x["row_span"]
                c.is_highlighted = [i, j] in entry["highlighted_cells"]
                c.is_col_header = x["is_header"] and i == 0
                c.is_row_header = x["is_header"] and i != 0
                table_obj.add_cell(c)

                for cs in range(x["column_span"]):
                    if cs:
                        c = Cell()
                        c.is_dummy = True
                        table_obj.add_cell(c)

                    for rs in range(x["row_span"]):
                        taken_cells.add((i + rs, col_num + cs))

                col_num += x["column_span"]

            table_obj.save_row()

        return table_obj

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

        t = self._write_cells(t, entry)

        return t
