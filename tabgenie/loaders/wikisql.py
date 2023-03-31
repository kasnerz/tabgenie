#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset


class WikiSQL(HFTabularDataset):
    """
    The WikiSQL dataset:
    https://github.com/salesforce/WikiSQL
    https://huggingface.co/datasets/wikisql (more processing included)
    Contains tables, SQL queries in machine- and human-readable representations,
        and questions based on tables.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = {}
        self.hf_id = "wikisql"
        self.name = "WikiSQL"
        self.extra_info = {"license": "BSD 3-Clause"}

    @staticmethod
    def _get_title(table):
        keys_to_try = ["caption", "section_title", "page_title"]
        for key in keys_to_try:
            value = table.get(key, "").strip()
            if value:
                return value

    def prepare_table(self, entry):
        t = Table()

        title = self._get_title(entry["table"])
        if title is not None:
            t.props["title"] = title

        t.props["sql"] = entry["sql"]["human_readable"]
        t.props["references"] = [entry["question"]]  # there are several questions per table but it's different SQLs
        t.props["id"] = entry["table"]["id"]
        t.props["name"] = entry["table"]["name"]

        for header_cell in entry["table"]["header"]:
            c = Cell()
            c.value = header_cell
            c.is_col_header = True
            t.add_cell(c)
        t.save_row()

        for row in entry["table"]["rows"]:
            for cell in row:
                c = Cell()
                c.value = cell
                t.add_cell(c)
            t.save_row()

        return t
