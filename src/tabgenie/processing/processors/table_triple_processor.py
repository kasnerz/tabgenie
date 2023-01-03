#!/usr/bin/env python3

from ..processing import Processor

class TableTripleProcessor(Processor):
    def process(self, content):
        dataset = content["dataset_obj"]
        triples = dataset.export_table(split=content["split"], table_idx=content["table_idx"], cell_ids=content["cells"], export_format="triples")

        return triples
