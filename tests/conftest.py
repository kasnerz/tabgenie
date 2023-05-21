import pytest  # pip install pytest==7.2.2
from tabgenie.loaders import DATASET_CLASSES


splits = [
    'dev',
    'test',
    'train'
]
tabs = [
    (key, spl)
    for key in DATASET_CLASSES
    for spl in splits
]


def id_func(data):
    return [f'{key}-{spl}' for key, spl in data]


@pytest.fixture(scope="session", params=tabs, ids=id_func(tabs))
def prepare_tests(request):
    dataset_name, split = request.param
    cls = DATASET_CLASSES[dataset_name]()
    cls.load(split)
    return dataset_name, split, cls
