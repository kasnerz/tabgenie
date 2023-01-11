#!/usr/bin/env python3
import logging

from ..processing import Pipeline
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
        self.processors = [TableTripleProcessor(), GraphProcessor()]

    def to_key(self, pipeline_args):
        cells = pipeline_args.get("cells", None)

        if cells:
            cells = str(set(cells))

        key = (pipeline_args["dataset"], pipeline_args["split"], pipeline_args["table_idx"], cells)
        return key