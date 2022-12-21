#!/usr/bin/env python3

from ..processing import Pipeline
from ..processors.graph_processor import GraphProcessor
from ..processors.text_ie_processor import TextIEProcessor

class TextIEPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [TextIEProcessor(), GraphProcessor()]
        
    def to_key(self, content):
        cells = content.get("cells", None)

        if cells:
            cells = str(set(cells))

        key = (content["dataset"], content["split"], content["table_idx"], cells)
        return key
