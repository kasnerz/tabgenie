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

    def _process_cell(
            self,
            table_obj,
            entry,
            raw_cell,
            row_num,
            raw_col_num,
            grid_col_num,
            row_is_header
    ):
        merged_cells = {}

        c = Cell()
        c.value = raw_cell["value"]
        c.colspan = raw_cell["column_span"]
        c.rowspan = raw_cell["row_span"]
        c.is_highlighted = [row_num, raw_col_num] in entry["highlighted_cells"]
        c.is_col_header = raw_cell["is_header"] and row_is_header
        c.is_row_header = raw_cell["is_header"] and not row_is_header
        table_obj.add_cell(c)

        for cs in range(raw_cell["column_span"]):
            for rs in range(raw_cell["row_span"]):
                if not cs and not rs:  # orig cell, already added
                    continue

                dc = self._create_dummy_cell(c, row_num, grid_col_num)
                if not rs:  # add cells which are on the same row
                    table_obj.add_cell(dc)
                else:  # for subsequent rows, save them and insert in the future
                    merged_cells[(row_num + rs, grid_col_num + cs)] = dc

        return table_obj, merged_cells

    def _write_cells(self, table_obj, entry):
        """
        So complicated because we need to restore
        the grid beneath the merged cells for simpler
        further automatic processing.
        """
        merged_cells = {}

        for i, row in enumerate(entry["table"]):
            col_num = 0
            while (i, col_num) in merged_cells:
                c = merged_cells[(i, col_num)]
                table_obj.add_cell(c)
                col_num += 1

            # if all cells in row are headers, then the row is column-wise header
            row_is_header = all(c['is_header'] for c in row)

            for j, x in enumerate(row):
                while (i, col_num) in merged_cells:
                    c = merged_cells[(i, col_num)]
                    table_obj.add_cell(c)
                    col_num += 1

                table_obj, curr_merged_cells = self._process_cell(
                    table_obj=table_obj,
                    entry=entry,
                    raw_cell=x,
                    row_num=i,
                    raw_col_num=j,
                    grid_col_num=col_num,
                    row_is_header=row_is_header

                )
                merged_cells.update(curr_merged_cells)

                col_num += x["column_span"]

            table_obj.save_row()

        return table_obj

    @staticmethod
    def _add_header_highlights(table_obj):
        for i, row in enumerate(table_obj.get_cells()):
            for j, c in enumerate(row):
                if not c.is_highlighted:
                    continue

                for cell in table_obj.get_col_headers(i, j) + table_obj.get_row_headers(i, j):
                    if not cell.value.strip():
                        continue

                    cell.is_highlighted = True
                    if cell.is_dummy:
                        main_cell = table_obj.get_cell(*cell.main_cell)
                        main_cell.is_highlighted = True

        return table_obj

    def prepare_table(self, entry):
        t = Table()
        t.props["references"] = entry["references"] or [entry["target"]]

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
