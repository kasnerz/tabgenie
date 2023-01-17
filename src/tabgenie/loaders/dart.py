#!/usr/bin/env python3
from datasets import load_dataset
from ..structs.data import Cell, Table, TabularDataset, HFTabularDataset
from ..utils.text import normalize

import logging 
logger = logging.getLogger(__name__)


class DART(HFTabularDataset):
    """
    The DART dataset: https://gem-benchmark.com/data_cards/dart
    A mixture of WebNLG, E2E and semi-new datasets created from WikiTableQuestions and WikiSQL.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "GEM/dart"
        self.name = "DART"

    def table_to_triples(self, table, cell_ids):
        triples = []
        rows = table.get_cells()[1:] # skip headers

        if any(len(x) != 3 for x in rows):
            logger.warning(f"Some triples do not have exactly 3 components {[x.value for x in row]}")

        for row in rows:
            triples.append([x.value for x in row])
        
        return triples

    def prepare_table(self, split, table_idx):
        entry = self.data[split][table_idx]
        t = Table()
        t.set_generated_output("reference", entry["target"])

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

        return t