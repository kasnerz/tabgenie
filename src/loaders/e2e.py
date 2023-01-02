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

    def table_to_triples(self, split, table_idx, cell_ids):
        table = self.get_table(split, table_idx)
        triples = []
        rows = table.get_cells()

        keys = [x.value for x in rows[0]]
        vals = [x.value for x in rows[1]]

        triples = []

        name_idx = None if "name" not in keys else keys.index("name")
        eatType_idx = None if "eatType" not in keys else keys.index("eatType")

        # primary option: use `name` as a subject
        if name_idx is not None:
            subj = vals[name_idx]
            del keys[name_idx]
            del vals[name_idx]

            # corrupted case hotfix
            if not keys:
                keys.append("eatType")
                vals.append("restaurant")

        # in some cases, that does not work -> use `eatType` as a subject
        elif eatType_idx is not None:
            subj = vals[eatType_idx]
            del keys[eatType_idx]
            del vals[eatType_idx]
        # still in some cases, there is not even an eatType 
        #-> hotfix so that we do not lose data
        else:
            # logger.warning(f"Cannot recognize subject in mr: {mr}")
            subj = "restaurant"

        for key, val in zip(keys, vals):
            triples.append([subj, key, val])

        # will be used as a key in a dictionary
        return triples


    def prepare_table(self, split, index):
        entry = self.data[split][index]
        t = Table()
        t.set_generated_output("reference", entry["target"])
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

        return t