#!/usr/bin/env python3
from openie import StanfordOpenIE

from ..processing import Processor


class TextIEProcessor(Processor):
    def __init__(self):
        super().__init__()

        self.openie_properties = {
            'openie.affinity_probability_cap': 2 / 3,
            'openie.triple.strict' : True
        }
        self.client = StanfordOpenIE(properties=self.openie_properties)


    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], table_idx=content["table_idx"])
        triples = self.client.annotate(table.ref)
        triples = [[t["subject"], t["relation"], t["object"]] for t in triples]

        return triples