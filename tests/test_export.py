import pytest
import json
from jsonschema import validate
from xlsxwriter.workbook import Workbook

from tabgenie.utils.export import *

'''-------------------JSON-SCHEMA-----------------------'''
# https://python-jsonschema.readthedocs.io/en/latest/
# need schema for testing tabs exporting into json
with open('tests/schemes/schema_without_prop.json') as f:
    schema_without_prop = json.load(f)

with open('tests/schemes/schema_with_prop.json') as f:
    schema_with_prop = json.load(f)
'''-----------------------------------------------------'''


def test_export_json(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        for prop in [True, False]:
            try:
                obj_json = json.dumps(table_to_json(table, prop))
                if not prop:
                    schema = schema_without_prop
                else:
                    schema = schema_with_prop
                validate(instance=obj_json, schema=schema)
            except:
                failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_excel(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        try:
            table_to_excel(table, include_props=True)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_csv(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        try:
            table_to_csv(table)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_df(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        try:
            table_to_df(table)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'


def test_export_html(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    html_format = ['web', 'export']
    include_props = [True, False]
    displayed_props = [None]
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        for form in html_format:
            for prop in include_props:
                try:
                    table_to_html(table, displayed_props, prop, form)
                except:
                    failed_nums.append(f'{nmb}-{prop}-{form}')

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'

"""
def test_export_triples(prepare_tests):
    tab, split, len_tab, cls = prepare_tests
    failed_nums = []
    cell_ids = None
    for nmb in range(len_tab):
        try:
            table = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        try:
            table_to_triples(table, cell_ids)
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'

"""
