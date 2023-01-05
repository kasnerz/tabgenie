#!/usr/bin/env python3

from ..processing import Processor

class ReferenceProcessor(Processor):
    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], table_idx=content["table_idx"])
        return self.text2html(table.ref)