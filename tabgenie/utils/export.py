#!/usr/bin/env python3
import pandas as pd
import lxml.etree
import lxml.html

from tinyhtml import h
from xlsxwriter import Workbook
from .excel import write_html_table_to_excel


"""
Default methods for exporting tables to various formats.
"""


def table_to_linear(
    table,
    cell_ids=None,
    include_props_mode="factual",  # 'all', 'factual', 'none'
    style="2d",  # 'index', 'markers', '2d'
    highlighted_only=False,
):
    prop_str = _table_props_to_linear(table, style=style, mode=include_props_mode)
    table_str = _table_content_to_linear(table, highlighted_only=highlighted_only, style=style, cell_ids=cell_ids)
    return prop_str + table_str


def table_to_json(table, include_props):
    j = {"data": [[c.__dict__ for c in row] for row in table.get_cells()]}

    if include_props and table.props is not None:
        j["properties"] = table.props

    return j


def table_to_triples(table, cell_ids):
    # TODO cell ids?
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


def table_to_excel(table, include_props=True):
    workbook = Workbook("tmp.xlsx", {"in_memory": True})
    worksheet = workbook.add_worksheet()
    write_html_table_to_excel(table, worksheet, workbook=workbook, write_table_props=include_props)

    return workbook


def table_to_csv(table):
    df = table_to_df(table)
    table_csv = df.to_csv(index=False)
    return table_csv


def table_to_df(table):
    table_el = _get_main_table_html(table)
    table_html = table_el.render()
    df = pd.read_html(table_html)[0]
    return df


def table_to_html(table, displayed_props, include_props, html_format):
    if html_format == "web" and table.props is not None:
        meta_el = _meta_to_html(table.props, displayed_props)
    elif html_format == "export" and include_props and table.props is not None:
        meta_el = _meta_to_simple_html(table.props)
    else:
        meta_el = None

    table_el = _get_main_table_html(table)
    area_el = h("div")(meta_el, table_el)

    html = area_el.render()
    return lxml.etree.tostring(lxml.html.fromstring(html), encoding="unicode", pretty_print=True)


def _table_content_to_linear(table, highlighted_only, style, cell_ids):
    tokens = []
    table_has_highlights = table.has_highlights()

    if cell_ids:
        cells = [[table.get_cell_by_id(int(idx)) for idx in cell_ids]]
    elif highlighted_only and table_has_highlights:
        cells = [table.get_highlighted_cells()]
    else:
        cells = table.get_cells()

    if style == "2d":
        for i, row in enumerate(cells):
            for j, cell in enumerate(row):
                tokens.append(f"| {cell.value} ")
            tokens.append(f"|\n")

    elif style == "markers":
        for i, row in enumerate(cells):
            tokens.append("[R] ")

            for j, cell in enumerate(row):
                tokens.append("[H] " if cell.is_header else "[C] ")
                tokens.append(cell.value + " ")

    elif style == "index":
        for i, row in enumerate(cells):
            for j, cell in enumerate(row):
                tokens.append(f"[{i}][{j}] ")
                tokens.append(cell.value + " ")

    return "".join(tokens)


def _table_props_to_linear(table, style, mode):
    # TODO arbitrary list of props
    if mode == "none" or not table.props:
        props_to_include = {}
    elif mode == "factual":
        props_to_include = {key: val for key, val in table.props.items() if "title" in key or "category" in key}
    elif mode == "all":
        props_to_include = table.props

    if not props_to_include:
        return ""

    if style == "2d":
        prop_tokens = [f"{key}: {val}" for key, val in props_to_include.items()]
    elif style == "markers" or "index":
        prop_tokens = [f"[P] {key}: {val}" for key, val in props_to_include.items()]

    if style == "2d":
        prop_str = "===================\n" + "\n".join(prop_tokens) + "\n===================\n"
    elif style == "markers" or "index":
        prop_str = " ".join(prop_tokens)

    return prop_str


def _meta_to_html(props, displayed_props):
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


def _meta_to_simple_html(props):
    meta_trs = []
    for key, value in props.items():
        meta_trs.append([h("th")(key), h("td")(value)])

    meta_tbodies = [h("tr")(tds) for tds in meta_trs]
    meta_tbody_el = h("tbody")(meta_tbodies)
    meta_table_el = h("table", klass="table table-sm caption-top meta-table")(h("caption")("properties"), meta_tbody_el)
    return meta_table_el


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
    table_el = h("table", klass="table table-sm table-bordered caption-top main-table")(h("caption")("data"), tbody_el)

    return table_el
