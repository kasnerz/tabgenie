#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset

# from ..utils.text import Detokenizer


class WikiBio(HFTabularDataset):
    """
    The WikiBio dataset
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "wiki_bio"
        self.name = "WikiBio"
        self.mapping = {}
        self.split_mapping = {"train": "train", "dev": "val", "test": "test"}

    @staticmethod
    def normalize(s):
        return s.replace("-lrb-", "(").replace("-rrb-", ")")

    def prepare_table(self, entry):
        t = Table()
        t.props["reference"] = entry["target_text"]
        t.props["title"] = self.normalize(entry["input_text"]["context"].rstrip("\n"))
        table = entry["input_text"]["table"]

        for key, val in zip(table["column_header"], table["content"]):
            # if val == "<none>":
            #     continue
            c = Cell(self.normalize(key))
            c.is_row_header = True
            t.add_cell(c)

            c = Cell(self.normalize(val))
            t.add_cell(c)

            t.save_row()

        return t
