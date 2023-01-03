#!/usr/bin/env python3

from ..processing import Processor

class LinearizeProcessor(Processor):
     def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], index=content["table_idx"])
        title = table.props.get("title")
        cells = [table.get_cell_by_id(int(cell_id)).value for cell_id in content["cells"]]

        s = [f"[TITLE] {title}"]

        for cell in cells:
            s.append(f"[CELL] {cell} [/CELL]")

        return " ".join(s)