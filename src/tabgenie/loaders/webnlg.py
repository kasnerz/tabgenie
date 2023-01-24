#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset
from ..utils.text import normalize

import logging

logger = logging.getLogger(__name__)


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

    def table_to_triples(self, table, cell_ids):
        triples = []
        rows = table.get_cells()[1:]  # skip headers

        if any(len(x) != 3 for x in rows):
            logger.warning(f"Some triples do not have exactly 3 components: {rows}")

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

        for triple in entry["input"]:
            elems = triple.split("|")
            for el in elems:
                c = Cell()
                c.value = normalize(el, remove_parentheses=False)
                t.add_cell(c)
            t.save_row()

        return t

    def get_task_definition(self):
        return "Write a short description of the following RDF triples."
