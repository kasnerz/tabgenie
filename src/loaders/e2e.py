#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, TabularDataset

from tinyhtml import h


class E2E(TabularDataset):
    """
    The Cleaned E2E dataset: https://huggingface.co/datasets/GEM/e2e_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """

    name = "e2e"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def load(self, split):
        dataset = load_dataset("gem", "e2e_nlg")

        data = dataset[split if split != "dev" else "validation"]
        self.data[split] = data
