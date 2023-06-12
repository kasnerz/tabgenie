import pytest
import json

from tabgenie.utils.export import *


def test_export_json(prepare_split):  # prepare_split is a fixture, the argument must have the same name as the fixture
    name, split, tables = prepare_split
    failed_nums = []
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        try:
            for prop in [True, False]:
                json.dumps(table_to_json(tables[nmb], prop))
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_excel(prepare_split):
    name, split, tables = prepare_split
    failed_nums = []
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        try:
            table_to_excel(tables[nmb], include_props=True)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_csv(prepare_split):
    name, split, tables = prepare_split
    failed_nums = []
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        try:
            table_to_csv(tables[nmb])
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_df(prepare_split):
    name, split, tables = prepare_split
    failed_nums = []
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        try:
            table_to_df(tables[nmb])
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_html(prepare_split):
    name, split, tables = prepare_split
    failed_nums = []
    html_format = ['web', 'export']
    include_props = [True, False]
    displayed_props = [None]
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        for form in html_format:
            for prop in include_props:
                try:
                    table_to_html(tables[nmb], displayed_props, prop, form)
                except:
                    failed_nums.append(f'{nmb}-{prop}-{form}')

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


"""
def test_export_triples(prepare_split):
    name, split, tables = prepare_split
    failed_nums = []
    cell_ids = None
    for nmb in range(len(tables)):
        if tables[nmb] is None:
            continue
        try:
            table_to_triples(tables[nmb], cell_ids)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{name}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'

"""
