#!/usr/bin/env python3
import ast

from ..structs.data import Cell, Table, HFTabularDataset


class Logic2Text(HFTabularDataset):
    """
    The Logic2Text dataset: https://github.com/czyssrs/Logic2Text
    Contains tables + explicit logical forms from which a utterance should be generated.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/logic2text"
        self.name = "Logic2Text"

    def prepare_table(self, entry):
        def is_highlighted(i, j):
            # these fields are not documented properly, possible cases were found manually
            # FIXME: "subset" is not handled properly
            if all(x in entry["annotation"] for x in ["row_1", "row_2", "col", "col_other"]):
                return (str(i + 1) == entry["annotation"]["row_1"] or str(i + 1) == entry["annotation"]["row_2"]) and (
                    str(j + 1) == entry["annotation"]["col"] or str(j + 1) == entry["annotation"]["col_other"]
                )
            elif all(x in entry["annotation"] for x in ["row", "col", "col_other"]):
                return str(i + 1) == entry["annotation"]["row"] and (
                    str(j + 1) == entry["annotation"]["col"] or str(j + 1) == entry["annotation"]["col_other"]
                )
            elif "col" in entry["annotation"]:
                return str(j + 1) == entry["annotation"]["col"]
            elif "col_superlative" in entry["annotation"] and "row_superlative" in entry["annotation"]:
                return (
                    (
                        str(j + 1) == entry["annotation"]["col_superlative"]
                        and str(i + 1) == entry["annotation"]["row_superlative"]
                    )
                    or (
                        "other_col" in entry["annotation"]
                        and str(j + 1) == entry["annotation"]["other_col"]
                        and str(i + 1) == entry["annotation"]["row_superlative"]
                    )
                    or (
                        "other_row" in entry["annotation"]
                        and str(j + 1) == entry["annotation"]["col_superlative"]
                        and str(i + 1) == entry["annotation"]["other_row"]
                    )
                )
            else:
                return False

        entry["annotation"] = ast.literal_eval(entry["annotation"])

        t = Table()
        t.props["references"] = [entry["sent"]]

        t.props["title"] = entry["topic"]
        t.props["url"] = entry["url"]
        t.props["wiki"] = entry["wiki"]
        t.props["action"] = entry["action"]
        t.props["interpret"] = entry["interpret"]
        t.props["logic_str"] = entry["logic_str"]
        t.props["annotation"] = str(entry["annotation"])

        for j, x in enumerate(ast.literal_eval(entry["table_header"])):
            c = Cell()
            c.value = x
            c.is_highlighted = is_highlighted(0, j)
            c.is_col_header = True
            t.add_cell(c)

        t.save_row()
        for i, row in enumerate(ast.literal_eval(entry["table_cont"])):
            for j, x in enumerate(row):
                c = Cell()
                c.value = x
                c.is_highlighted = is_highlighted(i, j)
                t.add_cell(c)

            t.save_row()

        return t
