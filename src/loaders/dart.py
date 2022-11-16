#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, TabularDataset, HFTabularDataset
from ..utils.text import normalize


class DART(HFTabularDataset):
    """
    The DART dataset: https://gem-benchmark.com/data_cards/dart
    A mixture of WebNLG, E2E and semi-new datasets created from WikiTableQuestions and WikiSQL.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/dart"

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]

        for val in ["subject", "predicate", "object"]:
            c = Cell()
            c.value = val
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()

        for triple in entry["tripleset"]:
            for el in triple:
                c = Cell()
                c.value = el
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t