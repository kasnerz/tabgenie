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

    def run_single(self, pipeline_args, example, export_format):

        if pipeline_args.get("dataset_objs") is not None:
            dataset_obj = pipeline_args["dataset_objs"][example["dataset"]]
        else:
            dataset_obj = pipeline_args["dataset_obj"]

        content = {
            "dataset_obj": dataset_obj,
            "export_format": export_format,
            "dataset": example["dataset"],
            "split": example["split"],
            "table_idx": example["table_idx"],
            "edited_cells": None,  # TODO
        }
        return self.processors[0].process(content)

    def run(self, pipeline_args, cache_only=False, force=True):
        # no caching

        if pipeline_args.get("export_format") is None:
            pipeline_args["export_format"] = pipeline_args["pipeline_cfg"].get("default_format") or "csv"

        if pipeline_args.get("json_template") is None:
            pipeline_args["json_template"] = "export/json_templates/default.yml"

        if pipeline_args.get("examples_to_export") is None:
            pipeline_args["examples_to_export"] = [
                {
                    "dataset": pipeline_args["dataset"],
                    "split": pipeline_args["split"],
                    "table_idx": pipeline_args["table_idx"],
                }
            ]

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
