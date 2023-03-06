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
    def _create_dummy_cell(main_cell, i, j):
        dc = Cell()
        dc.is_dummy = True
        dc.value = main_cell.value
        dc.is_col_header = main_cell.is_col_header
        dc.is_row_header = main_cell.is_row_header
        dc.main_cell = (i, j)
        return dc

    def _write_cells(self, table_obj, entry):
        """
        So complicated because we need to restore
        the grid beneath the merged cells for simpler
        further automatic processing.
        """
        taken_cells = {}

        for i, row in enumerate(entry["table"]):
            col_num = 0
            while (i, col_num) in taken_cells:
                c = taken_cells[(i, col_num)]
                table_obj.add_cell(c)
                col_num += 1

            for j, x in enumerate(row):
                while (i, col_num) in taken_cells:
                    c = taken_cells[(i, col_num)]
                    table_obj.add_cell(c)
                    col_num += 1

                c = Cell()
                c.value = x["value"]
                c.colspan = x["column_span"]
                c.rowspan = x["row_span"]
                c.is_highlighted = [i, j] in entry["highlighted_cells"]
                c.is_col_header = x["is_header"] and i == 0  # todo: col header annotation not in orig data?
                c.is_row_header = x["is_header"] and i != 0
                table_obj.add_cell(c)

                for cs in range(x["column_span"]):
                    for rs in range(x["row_span"]):
                        if not cs and not rs:  # orig cell, already added
                            continue

                        dc = self._create_dummy_cell(c, i, col_num)
                        if not rs:  # add cells which are on the same row
                            table_obj.add_cell(dc)
                        else:  # for subsequent rows, save them and insert in the future
                            taken_cells[(i + rs, col_num + cs)] = dc

                col_num += x["column_span"]

            table_obj.save_row()

        return table_obj

    @staticmethod
    def _add_header_highlights(table_obj):
        for i, row in enumerate(table_obj.get_cells()):
            for j, c in enumerate(row):
                if not c.is_highlighted:
                    continue

                for cell in table_obj.get_col_headers(j) + table_obj.get_row_headers(i):
                    cell.is_highlighted = True
                    if cell.is_dummy:
                        main_cell = table_obj.get_cell(*cell.main_cell)
                        main_cell.is_highlighted = True

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
        t = self._add_header_highlights(t)

        return t
