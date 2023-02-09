from bs4 import BeautifulSoup
from xlsxwriter import Workbook


def write_html_table_to_excel(table, workbook, worksheet, start_row=0, start_col=0):
    light_yellow = '#fffbcb'
    gray = '#b7b7b7'

    formats = {
        ('header', 'active'): workbook.add_format({'bold': True, 'bg_color': light_yellow, 'border': 1, 'border_color': gray}),
        ('header', None): workbook.add_format({'bold': True, 'border': 1, 'border_color': gray}),
        (None, 'active'): workbook.add_format({'bg_color': light_yellow, 'border': 1, 'border_color': gray}),
        (None, None): workbook.add_format({'border': 1, 'border_color': gray})
    }

    soup = BeautifulSoup(table, features='lxml')
    row_num = start_row

    for row in soup.find_all('tr'):
        col_num = start_col
        while (row_num, col_num) in worksheet.merged_cells:
            col_num += 1

        for cell in row.find_all(['th', 'td']):
            is_header = 'header' if cell.name == 'th' else None
            is_active = 'active' if 'table-active' in cell.attrs.get('class', []) else None
            cell_format = formats[(is_header, is_active)]

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

    return row_num


def write_annotation_to_excel(tables, prop_list, ann_columns, out_file):
    """
    Write multiple tables to excel for manual annotation.
    :param tables: List[Dict]: list of dicts, where dict is all info about the table,
                               including the table in HTML markup
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
            start_row=start_row, start_col=start_col
        )
        worksheet.set_row(end_row, None, delim_format)
        start_row = end_row + 1

    workbook.close()


if __name__ == '__main__':
    ann_columns = ['is_hallucination', 'notes']
    prop_list = ['title', 'reference']
    out_file = 'local_test.xlsx'

    tables = [
        {
            'table': """<table class="table table-sm table-bordered caption-top main-table">
                <caption>data</caption>
                <tbody id="main-table-body">
                  <tr>
                    <th colspan="1" rowspan="3" cell-idx="0" class="highlightable-cell">
                    </th><th colspan="2" rowspan="1" cell-idx="1" class="table-active highlightable-cell">women</th>
                    <th colspan="2" rowspan="1" cell-idx="3" class="highlightable-cell">men</th>
                  </tr>
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="6" class="highlightable-cell">canadian-born</th>
                    <th colspan="1" rowspan="1" cell-idx="7" class="table-active highlightable-cell">immigrants</th>
                    <th colspan="1" rowspan="1" cell-idx="8" class="highlightable-cell">canadian-born</th>
                    <th colspan="1" rowspan="1" cell-idx="9" class="highlightable-cell">immigrants</th>
                  </tr>
                  <tr>
                    <td colspan="4" rowspan="1" cell-idx="11" class="highlightable-cell">percent</td>
                  </tr>
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="15" class="table-active highlightable-cell">visible minority population</th>
                    <td colspan="1" rowspan="1" cell-idx="16" class="highlightable-cell">17</td>
                    <td colspan="1" rowspan="1" cell-idx="17" class="highlightable-cell">31</td>
                    <td colspan="1" rowspan="1" cell-idx="18" class="highlightable-cell">17</td>
                    <td colspan="1" rowspan="1" cell-idx="19" class="highlightable-cell">26</td>
                  </tr>
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="20" class="highlightable-cell">not a visible minority</th>
                    <td colspan="1" rowspan="1" cell-idx="21" class="highlightable-cell">14</td>
                    <td colspan="1" rowspan="1" cell-idx="22" class="highlightable-cell">21</td>
                    <td colspan="1" rowspan="1" cell-idx="23" class="highlightable-cell">16</td>
                    <td colspan="1" rowspan="1" cell-idx="24" class="highlightable-cell">19</td>
                  </tr>
                </tbody>
            </table>""",
            'table_id': 'hitab_dev_675',
            'title': 'overqualification rates among workers aged 25 to 34 with a university degree by sex, visible minority and immigrant status, canada, 2011',
            'reference': 'young visible minority women who were immigrants were more likely to be overqualified for their occupation than immigrant women who were not members of a visible minority group.',
        },
        {
            'table': """<table class="table table-sm table-bordered caption-top main-table">
                <caption>data</caption>
                <tbody id="main-table-body">
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="0" class="highlightable-cell">customer rating</th>
                    <td colspan="1" rowspan="1" cell-idx="1" class="highlightable-cell">average</td>
                  </tr>
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="2" class="highlightable-cell">area</th>
                    <td colspan="1" rowspan="1" cell-idx="3" class="highlightable-cell">riverside</td>
                  </tr>
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="4" class="highlightable-cell">near</th>
                    <td colspan="1" rowspan="1" cell-idx="5" class="highlightable-cell">Raja Indian Cuisine</td>
                  </tr>
                </tbody>
              </table>""",
            'table_id': 'e2e_dev_0',
            'reference': 'Over by the riverside, you can choose to dine at an average customer rated Travellers Rest Beefeaters, which is located near Raja Indian Cuisine.',
        },
        {
            'table': """<table class="table table-sm table-bordered caption-top main-table">
                <caption>data</caption>
                <tbody id="main-table-body">
                  <tr>
                    <th colspan="1" rowspan="1" cell-idx="0" class="highlightable-cell">subject</th>
                    <th colspan="1" rowspan="1" cell-idx="1" class="highlightable-cell">predicate</th>
                    <th colspan="1" rowspan="1" cell-idx="2" class="highlightable-cell">object</th>
                  </tr>
                  <tr>
                    <td colspan="1" rowspan="1" cell-idx="3" class="highlightable-cell">Arem-arem</td>
                    <td colspan="1" rowspan="1" cell-idx="4" class="highlightable-cell">country</td>
                    <td colspan="1" rowspan="1" cell-idx="5" class="highlightable-cell">Indonesia</td>
                  </tr>
                  <tr>
                    <td colspan="1" rowspan="1" cell-idx="6" class="highlightable-cell">Indonesia</td>
                    <td colspan="1" rowspan="1" cell-idx="7" class="highlightable-cell">leader</td>
                    <td colspan="1" rowspan="1" cell-idx="8" class="highlightable-cell">Joko Widodo</td>
                  </tr>
                  <tr>
                    <td colspan="1" rowspan="1" cell-idx="9" class="highlightable-cell">Indonesia</td>
                    <td colspan="1" rowspan="1" cell-idx="10" class="highlightable-cell">leader</td>
                    <td colspan="1" rowspan="1" cell-idx="11" class="highlightable-cell">Jusuf Kalla</td>
                  </tr>
                </tbody>
              </table>""",
            'table_id': 'webnlg_dev_899',
            'reference': 'Arem arem originates from the country of Indonesia, where two of the leaders are, Joko Widodo and Jusuf Kalla.'
        }
    ]

    write_annotation_to_excel(tables, prop_list, ann_columns, out_file)
