import pytest
from tabgenie.utils.export import *


def test_export_json(prepare_tests):  # prepare_tests is a fixture, the argument must have the same name as the fixture
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
            for prop in [True, False]:
                table_to_json(table, prop)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_excel(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
            table_to_excel(table, include_props=True)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_csv(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
            table_to_csv(table)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_df(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
            table_to_df(table)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_html(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    html_format = ['web', 'export']
    include_props = [True, False]
    displayed_props = [None]
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
        except:
            failed_nums.append(nmb)
            continue
        for form in html_format:
            for prop in include_props:
                try:
                    table_to_html(table, displayed_props, prop, form)
                except:
                    failed_nums.append(f'{nmb}-{prop}-{form}')

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


"""
def test_export_triples(prepare_tests):
    name, split, cls = prepare_tests
    failed_nums = []
    cell_ids = None
    for nmb, raw_table in enumerate(cls.data[split]):
        try:
            table = cls.prepare_table(raw_table)
            table_to_triples(table, cell_ids)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'

"""
