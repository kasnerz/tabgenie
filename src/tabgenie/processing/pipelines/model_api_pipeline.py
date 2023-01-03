#!/usr/bin/env python3
import logging

from ..processing import Pipeline
from ..processors.linearize_processor import LinearizeProcessor
from ..processors.model_api_processor import ModelAPIProcessor

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

class ModelAPIPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [LinearizeProcessor(), ModelAPIProcessor(model_url=self.cfg["model_url"])]

    def to_key(self, content):
        cells = content.get("cells", None)

        if cells:
            cells = str(set(cells))

        key = (content["dataset"], content["split"], content["table_idx"], cells)
        return key