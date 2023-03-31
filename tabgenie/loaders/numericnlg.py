#!/usr/bin/env python3
import ast

from ..structs.data import Cell, Table, HFTabularDataset


class NumericNLG(HFTabularDataset):
    """
    The NumericNLG dataset: https://github.com/titech-nlp/numeric-nlg
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_id = "kasnerz/numericnlg"
        self.name = "NumericNLG"

    def prepare_table(self, entry):
        t = Table()
        t.props["references"] = [entry["description"]]
        t.props["header_mention"] = entry["header_mention"]
        t.props["class_sentence"] = entry["header_mention"]
        t.props["table_id_paper"] = entry.get("table_id_paper")
        t.props["table_id"] = entry.get("table_id")
        t.props["title"] = entry["table_name"]
        t.props["caption"] = entry["caption"]
        t.props["dir"] = entry.get("dir")
        t.props["metrics_loc"] = entry.get("metrics_loc")
        t.props["metrics_type"] = str(entry.get("metrics_type") or "")
        t.props["paper_id"] = entry.get("paper_id")
        t.props["page_no"] = entry.get("page_no")
        t.props["target_entity"] = str(entry.get("target_entity") or "")
        t.props["valid"] = entry.get("valid")


        for i in range(int(entry["column_header_level"])):
            c = Cell("")
            c.colspan = int(entry["row_header_level"])
            c.is_col_header = True
            t.add_cell(c)

            for header_set in ast.literal_eval(entry["column_headers"]):
                try:
                    col = header_set[i]
                except IndexError:
                    col = ""
                c = Cell(col)
                # c.colspan = len(col)
                c.is_col_header = True
                t.add_cell(c)
            t.save_row()

        for i, row in enumerate(ast.literal_eval(entry["contents"])):
            row_headers = ast.literal_eval(entry["row_headers"])[i]

            for j, header in enumerate(row_headers):
                c = Cell(header)
                c.is_row_header = True
                t.add_cell(c)

            for j, x in enumerate(row):
                c = Cell(x)
                t.add_cell(c)
            t.save_row()

        return t
