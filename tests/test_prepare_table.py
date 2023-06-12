import pytest


def test_table(prepare_tests):  # prepare_tests is a fixture, the argument must have the same name as the fixture
    name, split, cls, num_of_tbl = prepare_tests
    failed_nums = []
    for nmb in range(num_of_tbl):
        try:
            cls.prepare_table(cls.data[split][nmb])
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
