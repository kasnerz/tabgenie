#!/usr/bin/env python3
import logging

from ..processing import Processor, Pipeline
from ..processors.linearize_processor import LinearizeProcessor
from ..processors.model_local_processor import ModelLocalProcessor

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class ModelLocalPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [LinearizeProcessor(), ModelLocalProcessor()]

