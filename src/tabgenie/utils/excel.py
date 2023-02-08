from bs4 import BeautifulSoup


def write_html_table_to_excel(table, workbook, worksheet, start_row=0, start_col=0):
    bold = workbook.add_format({'bold': True})
    soup = BeautifulSoup(table, features='lxml')
    row_num = start_row
    col_num = start_col

    for row in soup.find_all('tr'):
        col_num = start_col
        while (row_num, col_num) in worksheet.merged_cells:
            col_num += 1

        for cell in row.find_all(['th', 'td']):
            cell_format = bold if cell.name == 'th' else None

            colspan = int(cell.attrs.get('colspan', 1))
            rowspan = int(cell.attrs.get('rowspan', 1))
            if colspan > 1 or rowspan > 1:
                end_row = row_num + rowspan - 1
                end_col = col_num + colspan - 1
                worksheet.merge_range(
                    row_num, col_num,
                    end_row, end_col,
                    cell.text, cell_format
                )
            else:
                worksheet.write(row_num, col_num, cell.text, cell_format)

            col_num += colspan
        row_num += 1

    return col_num, row_num


def write_annotation_to_excel(tables, additional_columns, out_file):
    """
    Write multiple tables to excel for manual annotation.
    :param tables: dict: keys are table ids, values are tables in HTML markup
    :param additional_columns: list: list of additional column names to include in the table
    :param out_file: str: path for output file
    :return: None, results are written in the file
    """

    for table_id, table_html in tables.items():
        pass
