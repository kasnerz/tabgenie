#!/usr/bin/env python3
import re
import random

from ..processing import Processor


class CustomInputProcessor(Processor):

    @staticmethod
    def format_prompt(prompt, table, dataset, cell_ids):
        random.seed(42)
        rand_ex_split = "dev"
        prompt_vars = re.findall(r"\[PROMPTVAR:([\w]+)\]", prompt)
        rand_ex = set([x.group(1) for x in [re.match(r"^RAND(\d).*", y) for y in prompt_vars] if x is not None])
        ex_cnt = dataset.get_example_count(rand_ex_split)

        rand_tables = {}
        for x in rand_ex:
            ex_idx = random.randint(0, ex_cnt)
            rand_table = dataset.get_table(rand_ex_split, ex_idx)
            rand_tables[x] = rand_table

        prompt = re.sub(r"\[PROMPTVAR:TASK_DEF\]", dataset.get_task_definition(), prompt)
        prompt = re.sub(r"\[PROMPTVAR:TABLE_CSV\]", dataset.table_to_csv(table), prompt)
        prompt = re.sub(r"\[PROMPTVAR:HL_CELLS\]", dataset.table_to_linear(table, cell_ids), prompt)

        for x in rand_ex:
            prompt = re.sub(rf"\[PROMPTVAR:RAND{x}_TABLE_CSV\]", dataset.table_to_csv(rand_tables[x]), prompt)
            prompt = re.sub(rf"\[PROMPTVAR:RAND{x}_HL_CELLS\]", dataset.table_to_linear(rand_tables[x]), prompt)
            prompt = re.sub(rf"\[PROMPTVAR:RAND{x}_REF\]", dataset.get_reference(rand_tables[x]), prompt)

        return prompt

    def process(self, content):
        custom_input = content["custom_input"]

        table = content["dataset_obj"].get_table(
            content["split"], content["table_idx"], edited_cells=content.get("edited_cells")
        )
        custom_input = self.format_prompt(
            prompt=custom_input, table=table, dataset=content["dataset_obj"], cell_ids=content.get("cells")
        )

        return custom_input
