from .processing import Processor, Pipeline
from tinyhtml import h
import requests

class ReferencePipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [ReferenceProcessor()]

    def run(self, content, cache_only=False, force=False):
        # ignore cache_only or force, always just retrieve the reference
        next_inp = content
        for p in self.processors:
            next_inp = p.process(next_inp)

        out = next_inp
        return out


class ReferenceProcessor(Processor):
    def process(self, content):
        table = content["dataset_obj"].get_table(split=content["split"], index=content["table_idx"])
        return self.text2html(table.ref)