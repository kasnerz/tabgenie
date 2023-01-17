#!/usr/bin/env python3
import json
import os
import ast
from .data import Cell, Table, HFTabularDataset


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
        self.hf_id = 'wikisql'
        self.name = 'WikiSQL'

    @staticmethod
    def _get_title(table):
        keys_to_try = ['caption', 'section_title', 'page_title']
        for key in keys_to_try:
            value = table.get(key, '').strip()
            if value:
                return value

    def prepare_table(self, split, table_idx):
        entry = self.data[split][table_idx]
        t = Table()

        title = self._get_title(entry['table'])
        if title is not None:
            t.props['title'] = entry['table']['caption']
        t.props['sql'] = entry['sql']['human_readable']
        t.set_generated_output('reference', entry['question'])

        for header_cell in entry['table']['header']:
            c = Cell()
            c.value = header_cell
            c.is_col_header = True
            t.add_cell(c)
        t.save_row()

        for row in entry['table']['rows']:
            for cell in row:
                c = Cell()
                c.value = cell
                t.add_cell(c)
            t.save_row()

        return t
