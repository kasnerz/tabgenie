#!/usr/bin/env python3
import os
import copy
import logging

import datasets
import pandas as pd
import lxml.etree
import lxml.html

from tinyhtml import h


logger = logging.getLogger(__name__)


class Cell:
    """
    Table cell
    """

    def __init__(
        self,
        value=None,
        idx=None,
        colspan=1,
        rowspan=1,
        is_highlighted=False,
        is_col_header=False,
        is_row_header=False,
        is_dummy=False,
    ):
        self.idx = idx
        self.value = value
        self.colspan = colspan
        self.rowspan = rowspan
        self.is_highlighted = is_highlighted
        self.is_col_header = is_col_header
        self.is_row_header = is_row_header
        self.is_dummy = is_dummy

    @property
    def is_header(self):
        return self.is_col_header or self.is_row_header

    def __repr__(self):
        return str(self.__dict__)


class Table:
    """
    Table object
    """

    def __init__(self):
        self.props = {}
        self.cells = []
        self.outputs = {}
        self.url = None
        self.cell_idx = 0
        self.current_row = []
        self.cell_by_ids = {}

    def has_highlights(self):
        return any(cell.is_highlighted for row in self.cells for cell in row)

    def save_row(self):
        if self.current_row:
            self.cells.append(self.current_row)
            self.current_row = []

    def add_cell(self, cell):
        cell.idx = self.cell_idx
        self.current_row.append(cell)
        self.cell_by_ids[self.cell_idx] = cell
        self.cell_idx += 1

    def set_cell(self, i, j, c):
        self.cells[i][j] = c

    def get_cell(self, i, j):
        try:
            return self.cells[i][j]
        except:
            return None

    def get_cell_by_id(self, idx):
        return self.cell_by_ids[idx]

    def get_flat_cells(self, highlighted_only=False):
        return [x for row in self.cells for x in row if (x.is_highlighted or not highlighted_only)]

    def get_cells(self):
        return self.cells

    def get_row_headers(self, row_idx):
        try:
            cells_in_row = self.cells[row_idx]
            return [x for x in cells_in_row if x.is_row_header]
        except Exception as e:
            logger.exception(e)

    def get_col_headers(self, column_idx):
        try:
            cells_in_column = [row[column_idx] for row in self.cells]
            return [x for x in cells_in_column if x.is_col_header]
        except Exception as e:
            logger.exception(e)

    def get_generated_output(self, key):
        return self.outputs.get(key)

    def set_generated_output(self, key, value):
        self.outputs[key] = value

    def __repr__(self):
        return str(self.__dict__)


class TabularDataset:
    """
    Base class for the datasets
    """

    def __init__(self, path):
        self.splits = ["train", "dev", "test"]
        self.data = {split: [] for split in self.splits}
        self.tables = {split: {} for split in self.splits}
        self.path = path
        self.dataset_info = {}
        self.name = None

    def load(self, split, max_examples=None):
        """
        Load the dataset. Path can be specified for loading from a directory
        or omitted if the dataset is loaded from HF.
        """
        raise NotImplementedError

    @staticmethod
    def get_reference(table):
        return table.props.get("reference")

    def get_example_count(self, split):
        return len(self.data[split])

    def has_split(self, split):
        return bool(self.data[split])

    def get_table(self, split, table_idx, edited_cells=None):
        table = self.tables[split].get(table_idx)

        if not table:
            entry = self.data[split][table_idx]
            table = self.prepare_table(entry)
            self.tables[split][table_idx] = table

        if edited_cells:
            table_modif = copy.deepcopy(table)

            for cell_id, val in edited_cells.items():
                cell = table_modif.get_cell_by_id(int(cell_id))
                cell.value = val

            table = table_modif

        return table

    def prepare_table(self, entry):
        return NotImplementedError

    def get_info(self):
        return self.dataset_info

    def export_table(self, table, export_format, cell_ids=None, displayed_props=None):
        if export_format == "txt":
            exported = self.table_to_linear(table, cell_ids)
        elif export_format == "triples":
            exported = self.table_to_triples(table, cell_ids)
        elif export_format == "html":
            exported = self.table_to_html(table, displayed_props)
        elif export_format == "csv":
            exported = self.table_to_csv(table)
        elif export_format == "xlsx":
            # export table as object, writing directly to Excel worksheet later
            exported = table
        elif export_format == "reference":
            exported = self.get_reference(table)
        else:
            raise NotImplementedError(export_format)

        return exported

    def export(self, split, table_cfg):
        exported = []

        for i in range(self.get_example_count(split)):
            obj = {}
            for key, export_format in table_cfg["fields"].items():
                table = self.get_table(split, i)
                obj[key] = self.export_table(table, export_format=export_format)
            exported.append(obj)

        return exported

    @staticmethod
    def selected_cells_to_linear(table, cell_ids):
        tokens = []

        # selected cells -> 1D pos encoding  # todo: why separately? why 1D?
        cells = [table.get_cell_by_id(int(idx)) for idx in cell_ids]

        for i, cell in enumerate(cells):
            tokens.append(f"[{i}]")
            tokens.append(cell.value)

        return tokens

    @staticmethod
    def table_to_linear_2d(
            table,
            highlighted_only=False,
            separator='index'
    ):
        tokens = []
        table_has_highlights = table.has_highlights()

        # full table -> 2D pos encoding
        for i, row in enumerate(table.get_cells()):
            for j, cell in enumerate(row):
                if highlighted_only and table_has_highlights and not cell.is_highlighted:
                    continue

                if separator == 'structure':
                    if not j:  # start of row
                        tokens.append('[R]')
                    tokens.append('[H]' if cell.is_header else '[C]')
                else:
                    tokens.append(f"[{i}][{j}]")

                tokens.append(cell.value)

        return tokens

    def table_to_linear(
            self,
            table,
            separator='index',  # 'index', 'structure'
            highlighted_only=False,
            cell_ids=None,
    ):
        prop_tokens = []
        for prop in ["category", "title"]:
            if prop in table.props:
                prop_tokens.append(f"[{prop}] {table.props[prop]}")

        if cell_ids:
            table_tokens = self.selected_cells_to_linear(table, cell_ids)
        else:
            table_tokens = self.table_to_linear_2d(
                table,
                highlighted_only=highlighted_only,
                separator=separator
        )

        return " ".join(prop_tokens + table_tokens)

    def table_to_triples(self, table, cell_ids):
        # default method (dataset-agnostic)
        title = table.props.get("title")
        triples = []

        for i, row in enumerate(table.get_cells()):
            for j, cell in enumerate(row):
                if cell.is_header():
                    continue

                row_headers = table.get_row_headers(i)
                col_headers = table.get_col_headers(j)

                if row_headers and col_headers:
                    subj = row_headers[0].value
                    pred = col_headers[0].value

                elif row_headers and not col_headers:
                    subj = title
                    pred = row_headers[0].value

                elif col_headers and not row_headers:
                    subj = title
                    pred = col_headers[0].value

                obj = cell.value
                triples.append([subj, pred, obj])

        return triples

    def get_hf_dataset(
            self,
            split,
            tokenizer,
            linearize_fn=None,
            linearize_params=None,
            highlighted_only=True,
            max_length=512,
            num_proc=8
    ):
        # linearize tables and convert to input_ids
        # TODO num_proc acts weirdly in datasets 2.9.0, set temporarily to 1

        if linearize_params is None:
            linearize_params = {}

        if linearize_fn is None:
            linearize_fn = self.table_to_linear
            linearize_params['separator'] = 'structure'
            linearize_params['highlighted_only'] = highlighted_only

        def process_example(example):
            table_obj = self.prepare_table(example)
            linearized = linearize_fn(table_obj, **linearize_params)
            ref = self.get_reference(table_obj)

            tokens = tokenizer(linearized, max_length=max_length, truncation=True)
            ref_tokens = tokenizer(ref, max_length=max_length, truncation=True)
            tokens['labels'] = ref_tokens["input_ids"]

            return tokens

        logger.info(f"[tabgenie] linearizing tables using {linearize_fn}")
        lin_example = linearize_fn(self.prepare_table(self.data[split][0]), **linearize_params)
        logger.info(f"[tabgenie] linearized example ({split}/0): {lin_example}")

        processed_dataset = self.data[split].map(process_example, batched=False, num_proc=1)
        extra_columns = [
            col for col in processed_dataset.features.keys()
            if col not in ["labels", "input_ids", "attention_mask"]
        ]
        processed_dataset = processed_dataset.remove_columns(extra_columns)
        processed_dataset.set_format(type="torch")

        return processed_dataset

    def get_linearized_pairs(self, split, linearize_fn=None):
        if linearize_fn is None:
            linearize_fn = self.table_to_linear

        data = []
        for i, entry in enumerate(self.data[split]):
            ex = [
                linearize_fn(self.prepare_table(entry)),
                self.get_reference(self.get_table(split, i)),
            ]
            data.append(ex)

        return data

    def get_task_definition(self):
        # TODO implement for individual datasets
        return "Describe the following structured data in one sentence."

    def get_positive_examples(self):
        # TODO implement for individual datasets
        # TODO fix - split may not be loaded
        table_ex_1 = self.get_table("dev", 0)
        table_ex_2 = self.get_table("dev", 1)

        return [
            {
                "in": self.table_to_linear(table_ex_1),
                "out": self.get_reference(table_ex_1),
            },
            {
                "in": self.table_to_linear(table_ex_2),
                "out": self.get_reference(table_ex_2),
            },
        ]

    # def get_prompt(self, key):
    #     breakpoint()
    #     prompt = prompts[key]

    #     if "def" in key:
    #         definition = self.get_task_definition()
    #         prompt = prompt.format(definition=definition)

    #     if "pos" in key:
    #         ex = self.get_positive_examples()
    #         ex_1_in, ex_1_out, ex_2_in, ex_2_out = (
    #             ex[0]["in"].strip(),
    #             ex[0]["out"].strip(),
    #             ex[1]["in"].strip(),
    #             ex[1]["out"].strip(),
    #         )
    #         prompt = prompt.format(ex_1_in=ex_1_in, ex_1_out=ex_1_out, ex_2_in=ex_2_in, ex_2_out=ex_2_out)

    #     return prompt

    def table_to_csv(self, table):
        df = self.table_to_df(table)
        table_csv = df.to_csv(index=False)
        return table_csv

    def table_to_df(self, table):
        table_el = self._get_main_table_html(table)
        table_html = table_el.render()
        df = pd.read_html(table_html)[0]
        return df

    @staticmethod
    def meta_to_html(props, displayed_props):
        meta_tbodies = []
        meta_buttons = []

        for key, value in props.items():
            meta_row_cls = "collapse show" if key in displayed_props else "collapse"
            aria_expanded = "true" if key in displayed_props else "false"

            # two wrappers around text required for collapsing
            wrapper = h("div", klass=[meta_row_cls, f"row_{key}", "collapsible"])
            cells = [h("th")(wrapper(h("div")(key))), h("td")(wrapper(h("div")(value)))]

            meta_tbodies.append(h("tr")(cells))
            meta_buttons.append(
                h(
                    "button",
                    type_="button",
                    klass="prop-btn btn btn-outline-primary btn-sm",
                    data_bs_toggle="collapse",
                    data_bs_target=f".row_{key}",
                    aria_expanded=aria_expanded,
                    aria_controls=f"row_{key}",
                )(key)
            )

        prop_caption = h("div", id_="prop-caption")("properties")
        meta_buttons_div = h("div", klass="prop-buttons")(meta_buttons)
        meta_tbody_el = h("tbody")(meta_tbodies)
        meta_table_el = h("table", klass="table table-sm table-borderless caption-top meta-table")(meta_tbody_el)
        meta_el = h("div")(prop_caption, meta_buttons_div, meta_table_el)
        return meta_el

    def table_to_html(self, table, displayed_props):
        meta_el = self.meta_to_html(table.props, displayed_props) if table.props else None
        table_el = self._get_main_table_html(table)
        area_el = h("div")(meta_el, table_el)

        html = area_el.render()
        return lxml.etree.tostring(lxml.html.fromstring(html), encoding="unicode", pretty_print=True)

    @staticmethod
    def _get_main_table_html(table):
        trs = []
        for row in table.cells:
            tds = []
            for c in row:
                if c.is_dummy:
                    continue

                eltype = "th" if c.is_header else "td"
                td_el = h(eltype, colspan=c.colspan, rowspan=c.rowspan, cell_idx=c.idx)(c.value)

                if c.is_highlighted:
                    td_el.tag.attrs["class"] = "table-active"

                tds.append(td_el)
            trs.append(tds)

        tbodies = [h("tr")(tds) for tds in trs]
        tbody_el = h("tbody", id="main-table-body")(tbodies)
        table_el = h("table", klass="table table-sm table-bordered caption-top main-table")(
            h("caption")("data"), tbody_el
        )

        return table_el


class HFTabularDataset(TabularDataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, path=None, **kwargs)
        self.hf_id = None  # needs to be set
        self.hf_extra_config = None
        self.split_mapping = {"train": "train", "dev": "validation", "test": "test"}
        self.dataset_info = {}
        self.extra_info = {}

    def _load_split(self, split):
        hf_split = self.split_mapping[split]

        logger.info(f"Loading {self.hf_id}/{split}")
        dataset = datasets.load_dataset(
            self.hf_id,
            name=self.hf_extra_config,
            split=hf_split,
            num_proc=4,
        )
        self.dataset_info = dataset.info.__dict__
        self.data[split] = dataset

    def load(self, split=None, max_examples=None):
        if max_examples is not None:
            logger.warning("The `max_examples` parameter is not currently supported for HF datasets")

        if split is None:
            for split in self.split_mapping.keys():
                self._load_split(split)
        else:
            self._load_split(split)

    def save_to_disk(self, split, filepath):
        self.data[split].save_to_disk(filepath)
        logger.info(f"File {filepath} saved successfully")

    def load_from_disk(self, split, filepath):
        self.data[split] = datasets.load_dataset(filepath)

    def get_info(self):
        info = {key: self.dataset_info.get(key) for key in ["citation", "description", "version", "license"]}
        info["examples"] = {}
        info["links"] = {}

        for split_name, split_info in self.dataset_info.get("splits").items():
            if split_name.startswith("val"):
                split_name = "dev"

            if split_name not in ["train", "dev", "test"]:
                continue

            info["examples"][split_name] = split_info.num_examples

        if info["version"] is not None:
            info["version"] = str(info["version"])

        if self.dataset_info.get("homepage"):
            info["links"]["homepage"] = self.dataset_info["homepage"]
        elif self.extra_info.get("homepage"):
            info["links"]["homepage"] = self.extra_info["homepage"]

        info["links"]["source"] = "https://huggingface.co/datasets/" + self.hf_id
        info["name"] = self.name

        # some info may not be present on HF, set it manually
        info.update(self.extra_info)

        return info
