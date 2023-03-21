import pytest
from tabgenie.loaders import DATASET_CLASSES

splits = [
    'dev',
    'test',
    'train'
]
tabs = [key
        for key in DATASET_CLASSES
        ]


@pytest.mark.parametrize('split', splits)
@pytest.mark.parametrize('tab', tabs)
def test_table(split, tab):
    cls = DATASET_CLASSES[tab]()
    cls.load(split)

    failed_nums = []
    for nmb in range(len(cls.data[split])):
        try:
            cls.prepare_table(cls.data[split][nmb])
        except:
            failed_nums.append(nmb)

    assert not failed_nums, \
        f'{tab}-{split}\n' \
        f'Count error tables - {len(failed_nums)}\n' \
        f'First 20 numbers - {failed_nums[:20]}'
