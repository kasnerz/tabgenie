import pytest
from tabgenie.loaders import DATASET_CLASSES
#pip install pytest==7.2.2




splits = [
    'dev',
    'test',
    'train'
]
tabs = [(key, spl)
        for key in DATASET_CLASSES
        for spl in splits
        ]

def id_func(data):
    return [f'{key}-{spl}' for key, spl in data]


@pytest.fixture(scope="session", params=tabs, ids=id_func(tabs))
def prepare_tests(request):
    tab, split = request.param
    cls = DATASET_CLASSES[tab]()
    cls.load(split)
    len_tab = len(cls.data[split])
    return tab, split, len_tab, cls
