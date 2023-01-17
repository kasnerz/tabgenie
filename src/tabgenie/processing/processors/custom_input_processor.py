#!/usr/bin/env python3

from ..processing import Processor
from tabgenie.utils.text import format_prompt
import re


class CustomInputProcessor(Processor):
    def process(self, content):
        custom_input = content["custom_input"]

        table = content["dataset_obj"].get_table(
            content["split"], content["table_idx"], edited_cells=content.get("edited_cells")
        )

        custom_input = format_prompt(
            prompt=custom_input, table=table, dataset=content["dataset_obj"], cell_ids=content.get("cells")
        )

        return custom_input
