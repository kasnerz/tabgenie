import pytest


def test_row_eq_len(prepare_tests):  # prepare_tests is a fixture, the argument must have the same name as the fixture
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
        except:
            failed_nums.append(nmb)
            continue
        cells = table.get_cells()
        same_length = all(len(row) == len(cells[0]) for row in cells)
        if not same_length:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
