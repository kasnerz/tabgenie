#!/usr/bin/env python3
from ..processing import Processor


class TableTripleProcessor(Processor):
    def process(self, content):
        dataset = content["dataset_obj"]

        table = dataset.get_table(
            split=content["split"], table_idx=content["table_idx"], edited_cells=content.get("edited_cells")
        )

        triples = dataset.export_table(table=table, cell_ids=content.get("cells", None), export_format="triples")

        return triples
