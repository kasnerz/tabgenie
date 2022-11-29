#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, HFTabularDataset

from tinyhtml import h


class E2E(HFTabularDataset):
    """
    The Cleaned E2E dataset: https://huggingface.co/datasets/GEM/e2e_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = 'GEM/e2e_nlg'
        self.name = "E2E"

    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.ref = entry["target"]
        mrs = entry["meaning_representation"].split(", ")

        for mr in mrs:
            key = mr.split("[")[0]
            c = Cell()
            c.value = key
            c.is_col_header = True
            t.add_cell(c)
        t.save_row()

        for mr in mrs:
            value = mr.split("[")[1][:-1]
            c = Cell()
            c.value = value
            t.add_cell(c)
        t.save_row()

        self.tables[split][index] = t
        return t