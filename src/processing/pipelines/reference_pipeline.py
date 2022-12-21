#!/usr/bin/env python3

from ..processing import Pipeline
from ..processors.reference_processor import ReferenceProcessor

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