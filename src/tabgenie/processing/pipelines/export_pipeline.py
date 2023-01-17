#!/usr/bin/env python3
import logging
import pip
import yaml

from ..processing import Pipeline
from ..processors.export_processor import ExportProcessor


logger = logging.getLogger(__name__)


class ExportPipeline(Pipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processors = [ExportProcessor()]

    def run_single(self, pipeline_args, example, export_format):
        content = {
            "dataset_obj": pipeline_args["dataset_objs"][example["dataset"]],
            "export_format": export_format,
            "dataset": example["dataset"],
            "split": example["split"],
            "table_idx": example["table_idx"],
            "edited_cells": None,  # TODO
        }
        return self.processors[0].process(content)

    def run(self, pipeline_args, cache_only=False, force=True):
        # no caching
        if pipeline_args["export_format"] == "json":
            with open(pipeline_args["json_template"]) as f:
                template = yaml.safe_load(f)
                table_key = template["table_key"]
                table_fields = template["table_fields"]

            out = {table_key: []}
        else:
            out = []

        for example in pipeline_args["examples_to_export"]:
            if pipeline_args["export_format"] == "json":
                out_ex = {}

                for key, export_format in table_fields.items():
                    out_ex[key] = self.run_single(pipeline_args, example, export_format)

                out[table_key].append(out_ex)
            else:
                export_format = pipeline_args["export_format"]

                out.append(self.run_single(pipeline_args=pipeline_args, example=example, export_format=export_format))

        return out
