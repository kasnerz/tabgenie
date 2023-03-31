#!/usr/bin/env python3
from ..structs.data import Cell, Table, HFTabularDataset
from ..utils.text import normalize
import ast
import logging

logger = logging.getLogger(__name__)


class CACAPO(HFTabularDataset):
    """
    The CAPAPO dataset: https://github.com/TallChris91/CACAPO-Dataset
    Contains sentences from news reports for the sports, weather, stock, and incidents domain in English and Dutch, aligned with relevant attribute-value paired data.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/cacapo"
        self.name = "CACAPO"

    def prepare_table(self, entry):
        t = Table()
        refs = [ast.literal_eval(item)[0] for item in entry["lex"]["text"]]
        t.props["references"] = refs  # todo: doesn't seem that there are more than 1 but there should be, according to paper
        t.props["category"] = entry["category"]
        t.props["lang"] = entry["lang"]
        keyvals = entry["modified_triple_sets"]["mtriple_set"][0]

        for keyval in keyvals:
            key, value = keyval.split(" | ")
            c = Cell()
            c.value = key
            c.is_row_header = True
            t.add_cell(c)

            c = Cell()
            c.value = value
            t.add_cell(c)

            t.save_row()

        return t
