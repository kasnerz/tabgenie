import pytest
import json
from jsonschema import validate

from tabgenie.utils.export import table_to_json

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
            tab = cls.prepare_table(cls.data[split][nmb])
        except:
            pytest.skip('test_table is failed')
        for prop in [True, False]:
            obj_json = json.dumps(table_to_json(tab, prop))
            if not prop:
                schema = schema_without_prop
            else:
                schema = schema_with_prop
            try:
                validate(instance=obj_json, schema=schema)
            except:
                failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
