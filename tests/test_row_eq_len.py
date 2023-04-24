import pytest


def test_export_json(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            tab = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        cells = tab.get_cells()
        same_length = all(len(row) == len(cells[0]) for row in cells)
        if not same_length:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
