#!/usr/bin/env python3
from datasets import load_dataset
from .data import Cell, Table, TabularDataset, HFTabularDataset
from ..utils.text import normalize


class WebNLG(HFTabularDataset):
    """
    The WebNLG dataset: https://huggingface.co/datasets/GEM/web_nlg
    Contains DBPedia triples and their crowdsourced verbalizations.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/web_nlg"
        self.hf_extra_config = "en"
        self.name = "WebNLG"

    def _export_triples(self, split, table_idx, cell_ids):
        table = self.get_table(split, table_idx)
        triples = []
        rows = table.get_cells()[1:] # skip headers

        for row in rows:
            triples.append([x.value for x in row])
        
        assert all(len(triple) == 3 for triple in triples)

        return triples


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

        for triple in entry["input"]:
            elems = triple.split("|")
            for el in elems:
                c = Cell()
                c.value = normalize(el, remove_parentheses=False)
                t.add_cell(c)
            t.save_row()

        self.tables[split][index] = t
        return t