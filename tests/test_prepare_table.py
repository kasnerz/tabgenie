import pytest


def test_table(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            cls.prepare_table(cls.data[split][nmb])
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
