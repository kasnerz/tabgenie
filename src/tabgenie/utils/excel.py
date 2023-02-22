from xlsxwriter import Workbook


COLORS = {
    'light_yellow': '#fffbcb',
    'light_gray': '#ececec',
    'gray': '#b7b7b7'
}

STYLES = {
    'data_table': {'border': 1, 'border_color': COLORS['gray']},
    'data_table_header': {'bold': True, 'border': 1, 'border_color': COLORS['gray']},
    'data_table_active': {'bg_color': COLORS['light_yellow'], 'border': 1, 'border_color': COLORS['gray']},
    'data_table_header_active': {
        'bold': True, 'bg_color': COLORS['light_yellow'],
        'border': 1, 'border_color': COLORS['gray']
    },
    'bold': {'bold': True},
    'ann_table_header': {
        'bold': True, 'bg_color': COLORS['light_gray'],
        'border': 1, 'border_color': COLORS['gray']
    },
    'ann_table_delim': {
        'bold': True, 'bg_color': COLORS['light_gray'],
        'top': 1, 'top_color': COLORS['gray'],
        'bottom': 1, 'bottom_color': COLORS['gray'],
    }
}


def write_merged_cells(cell, row_num, col_num, merge_cells, merged_cells, worksheet, cell_format):
    end_row = row_num + cell.rowspan - 1
    end_col = col_num + cell.colspan - 1

    for r in range(row_num, end_row + 1):
        for c in range(col_num, end_col + 1):
            merged_cells.add((r, c))
            if not merge_cells:  # setting the format for all cells separately
                worksheet.write(r, c, '', cell_format)

    if merge_cells:
        worksheet.merge_range(
            row_num, col_num,
            end_row, end_col,
            cell.value, cell_format
        )
    else:
        worksheet.write(row_num, col_num, cell.value, cell_format)

    return merged_cells


def write_html_table_to_excel(
        table,
        worksheet,
        style_objs=None,
        workbook=None,
        start_row=0,
        start_col=0,
        merge_cells=True
):
    if style_objs is None:
        # TODO this will fail if workbook is None
        style_objs = {k: workbook.add_format(v) for k, v in STYLES.items()}

    row_num = start_row
    merged_cells = set()

    for row in table.cells:
        col_num = start_col
        while (row_num, col_num) in merged_cells:
            col_num += 1

        for cell in row:
            if cell.is_dummy:
                continue

            while (row_num, col_num) in merged_cells:
                col_num += 1

            style_key = 'data_table'
            if cell.is_col_header or cell.is_row_header:
                style_key += '_header'
            if cell.is_highlighted:
                style_key += '_active'
            cell_format = style_objs[style_key]

            if cell.colspan > 1 or cell.rowspan > 1:
                merged_cells = write_merged_cells(
                    cell, row_num, col_num, merge_cells, merged_cells, worksheet, cell_format
                )
            else:
                worksheet.write(row_num, col_num, cell.value, cell_format)

            col_num += cell.colspan
        row_num += 1

    return row_num


def write_annotation_to_excel(tables, prop_list, ann_columns, out_file):
    """
    Write multiple tables to excel for manual annotation.
    :param tables: List[Dict]: list of dicts, where dict is all info about the table,
                               including the table as a `Table` object
    :param prop_list: List[str]: list of properties that are selected by the user
                                 to be included in the annotation
    :param ann_columns: List[str]: list of additional annotation columns to include in the annotation table
    :param out_file: str: path for output file
    :return: None, results are written in the file
    """

    workbook = Workbook(out_file)
    worksheet = workbook.add_worksheet()
    style_objs = {k: workbook.add_format(v) for k, v in STYLES.items()}

    ann_header = ['table_id'] + ann_columns  # all annotation columns
    worksheet.write_row(0, 0, ann_header + ['property_name', 'property_value', 'table'])
    worksheet.set_row(0, None, style_objs['ann_table_header'])

    start_row = 1
    start_col = len(ann_header)

    for table_info in tables:
        # writing table id
        worksheet.write(start_row, 0, table_info.get('table_id', ''))

        # writing properties
        props_end_row = start_row + len(prop_list)
        for i, prop_name in enumerate(prop_list):
            worksheet.write(start_row + i, start_col, prop_name, style_objs['bold'])
            worksheet.write(start_row + i, start_col + 1, table_info.get(prop_name, ''))

        # writing table
        table_end_row = write_html_table_to_excel(
            table_info['table'], worksheet, style_objs=style_objs,
            start_row=start_row, start_col=start_col + 2,
            merge_cells=False
        )

        # writing delimiter
        end_row = max(props_end_row, table_end_row)
        worksheet.set_row(end_row, None, style_objs['ann_table_delim'])
        start_row = end_row + 1

    workbook.close()


if __name__ == '__main__':
    from src.tabgenie.loaders.e2e import E2E
    from src.tabgenie.loaders.hitab import HiTab
    from src.tabgenie.loaders.webnlg import WebNLG

    ann_columns = ['is_hallucination', 'notes']
    prop_list = ['title', 'reference']
    out_file = 'local_test.xlsx'

    h = HiTab(path=None)
    h.load('dev')

    e = E2E(path=None)
    e.load('dev')

    w = WebNLG(path=None)
    w.load('dev')
    
    tables = [
        {
            'table': h.prepare_table(h.data['dev'][675]),
            'table_id': 'hitab_dev_675',
            'title': 'overqualification rates among workers aged 25 to 34 with a university degree by sex, visible minority and immigrant status, canada, 2011',
            'reference': 'young visible minority women who were immigrants were more likely to be overqualified for their occupation than immigrant women who were not members of a visible minority group.',
        },
        {
            'table': e.prepare_table(e.data['dev'][0]),
            'table_id': 'e2e_dev_0',
            'reference': 'Over by the riverside, you can choose to dine at an average customer rated Travellers Rest Beefeaters, which is located near Raja Indian Cuisine.',
        },
        {
            'table': w.prepare_table(w.data['dev'][899]),
            'table_id': 'webnlg_dev_899',
            'reference': 'Arem arem originates from the country of Indonesia, where two of the leaders are, Joko Widodo and Jusuf Kalla.'
        }
    ]

    write_annotation_to_excel(tables, prop_list, ann_columns, out_file)