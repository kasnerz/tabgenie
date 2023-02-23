#!/usr/bin/env python3
import logging

import yaml

from ..processing import Pipeline
from ..processors.export_processor import ExportProcessor


logger = logging.getLogger(__name__)


class ExportPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [ExportProcessor()]

    def run_single(self, pipeline_args, example):
        if pipeline_args.get("dataset_objs") is not None:
            dataset_obj = pipeline_args["dataset_objs"][example["dataset"]]
        else:
            dataset_obj = pipeline_args["dataset_obj"]

        export_format = pipeline_args["export_format"]
        linearization_style = pipeline_args["linearization_style"]
        edited_cells = pipeline_args.get("edited_cells")

        content = {
            "dataset_obj": dataset_obj,
            "export_format": export_format,
            "linearization_style": linearization_style,
            "dataset": example["dataset"],
            "split": example["split"],
            "table_idx": example["table_idx"],
            "include_props": pipeline_args["include_props"],
            "edited_cells": edited_cells,  # TODO
        }
        return self.processors[0].process(content)

    def run(self, pipeline_args, cache_only=False, force=True):
        # no caching
        out = []

        for i, example in enumerate(pipeline_args["examples_to_export"]):
            if i % 100 == 0:
                logger.info(f"Exported {i+1} example(s)")

            out.append(self.run_single(pipeline_args=pipeline_args, example=example))

        logger.info(f"Exported {i+1} example(s)")

        return out
