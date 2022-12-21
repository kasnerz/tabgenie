#!/usr/bin/env python3
import logging

from ..processing import Pipeline
from ..processors.text_ie_processor import TextIEProcessor
from ..processors.graph_processor import GraphProcessor
from ..processors.table_triple_processor import TableTripleProcessor

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

class GraphPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [TextIEProcessor(), GraphProcessor()]

    def to_key(self, content):
        cells = content.get("cells", None)

        if cells:
            cells = str(set(cells))

        key = (content["dataset"], content["split"], content["table_idx"], cells)
        return key