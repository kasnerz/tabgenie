from xlsxwriter import Workbook


def write_merged_cells(cell, row_num, col_num, merge_cells, merged_cells, worksheet, cell_format):
    end_row = row_num + cell.rowspan - 1
    end_col = col_num + cell.colspan - 1

    if merge_cells:
        worksheet.merge_range(
            row_num, col_num,
            end_row, end_col,
            cell.value, cell_format
        )
    else:
        worksheet.write(row_num, col_num, cell.value, cell_format)

    for r in range(row_num, end_row + 1):
        for c in range(col_num, end_col + 1):
            merged_cells.add((r, c))

    return merged_cells


def write_html_table_to_excel(table, workbook, worksheet, start_row=0, start_col=0, merge_cells=True):
    row_num = start_row
    merged_cells = set()

    light_yellow = '#fffbcb'
    gray = '#b7b7b7'

    formats = {
        ('header', 'active'): workbook.add_format({'bold': True, 'bg_color': light_yellow, 'border': 1, 'border_color': gray}),
        ('header', None): workbook.add_format({'bold': True, 'border': 1, 'border_color': gray}),
        (None, 'active'): workbook.add_format({'bg_color': light_yellow, 'border': 1, 'border_color': gray}),
        (None, None): workbook.add_format({'border': 1, 'border_color': gray})
    }

    for row in table.cells:
        col_num = start_col
        while (row_num, col_num) in merged_cells:
            col_num += 1

        for cell in row:
            if cell.is_dummy:
                continue

            is_header = 'header' if cell.is_col_header or cell.is_row_header else None
            is_active = 'active' if cell.is_highlighted else None
            cell_format = formats[(is_header, is_active)]

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
    light_gray = '#ececec'
    gray = '#b7b7b7'
    workbook = Workbook(out_file)
    worksheet = workbook.add_worksheet()
    header_format = workbook.add_format({'bold': True, 'bg_color': light_gray, 'border': 1, 'border_color': gray})
    delim_format = workbook.add_format({'bold': True, 'bg_color': light_gray})

    header = ['table_id'] + prop_list + ann_columns  # all columns except for table
    worksheet.write_row(0, 0, header)
    worksheet.write(0, len(header), 'table')
    worksheet.set_row(0, None, header_format)

    start_row = 1
    start_col = len(header)
    for table_info in tables:
        row = [table_info.get(k, '') for k in header]
        worksheet.write_row(start_row, 0, row)
        end_row = write_html_table_to_excel(
            table_info['table'], workbook, worksheet,
            start_row=start_row, start_col=start_col,
            merge_cells=False
        )
        worksheet.set_row(end_row, None, delim_format)
        start_row = end_row + 1

    workbook.close()


# ann_columns = ['is_hallucination', 'notes']
# prop_list = ['title', 'reference']
# out_file = 'local_test.xlsx'
#
# tables = [
#     {
#         'table': "`Table` object here",
#         'table_id': 'hitab_dev_675',
#         'title': 'overqualification rates among workers aged 25 to 34 with a university degree by sex, visible minority and immigrant status, canada, 2011',
#         'reference': 'young visible minority women who were immigrants were more likely to be overqualified for their occupation than immigrant women who were not members of a visible minority group.',
#     },
#     {
#         'table': "`Table` object here",
#         'table_id': 'e2e_dev_0',
#         'reference': 'Over by the riverside, you can choose to dine at an average customer rated Travellers Rest Beefeaters, which is located near Raja Indian Cuisine.',
#     },
#     {
#         'table': "`Table` object here",
#         'table_id': 'webnlg_dev_899',
#         'reference': 'Arem arem originates from the country of Indonesia, where two of the leaders are, Joko Widodo and Jusuf Kalla.'
#     }
# ]
#
# write_annotation_to_excel(tables, prop_list, ann_columns, out_file)
