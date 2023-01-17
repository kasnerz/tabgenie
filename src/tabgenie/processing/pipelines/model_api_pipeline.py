#!/usr/bin/env python3
import logging

from ..processing import Pipeline
from ..processors.custom_input_processor import CustomInputProcessor
from ..processors.model_api_processor import ModelAPIProcessor

logger = logging.getLogger(__name__)


class ModelAPIPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [CustomInputProcessor(), ModelAPIProcessor(model_url=self.cfg["model_url"])]

    def to_key(self, pipeline_args):
        cells = pipeline_args.get("cells", None)
        custom_input = pipeline_args.get("custom_input", None)

        if cells:
            cells = str(set(cells))

        key = (pipeline_args["dataset"], pipeline_args["split"], pipeline_args["table_idx"], cells, custom_input)
        return key
