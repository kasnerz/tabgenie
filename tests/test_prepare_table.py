import pytest


def test_table(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            cls.prepare_table(raw_table)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
