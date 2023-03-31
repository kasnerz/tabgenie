#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset
from ..utils.text import normalize
import ast
import logging

logger = logging.getLogger(__name__)


class EventNarrative(HFTabularDataset):
    """
    The EventNarrative dataset: https://www.kaggle.com/datasets/acolas1/eventnarration
    A knowledge graph-to-text dataset from publicly available open-world knowledge graphs, focusing on event-centric data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/eventnarrative"
        self.name = "EventNarrative"

    def table_to_triples(self, table, cell_ids):
        triples = []
        rows = table.get_cells()[1:]  # skip headers

        if any(len(x) != 3 for x in rows):
            logger.warning(f"Some triples do not have exactly 3 components: {rows}")

        for row in rows:
            triples.append([x.value for x in row])

        return triples

    def prepare_table(self, entry):
        reference = entry["narration"]

        for key, val in ast.literal_eval(entry["entity_ref_dict"]).items():
            reference = reference.replace(key, val)

        t = Table()
        t.props["references"] = [reference]
        t.props["title"] = entry["Event_Name"]
        t.props["types"] = entry["types"]
        t.props["reference_delex"] = entry["narration"]
        t.props["entity_ref_dict"] = entry["entity_ref_dict"]
        t.props["wikipediaLabel"] = entry["wikipediaLabel"]

        triples = ast.literal_eval(entry["keep_triples"])

        for val in ["subject", "predicate", "object"]:
            c = Cell()
            c.value = val
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()

        for triple in triples:
            for el in triple:
                c = Cell()
                c.value = normalize(el, remove_parentheses=False)
                t.add_cell(c)
            t.save_row()

        return t
