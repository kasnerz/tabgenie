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
def prepare_split(request):
    dataset_name, split = request.param
    cls = DATASET_CLASSES[dataset_name]()
    cls.load(split)
    num_of_tbl = len(cls.data[split])
    p_tabs = [None for _ in range(num_of_tbl)]
    err_tabs = []
    for nmb in range(num_of_tbl):
        try:
            p_tabs[nmb] = cls.prepare_table(cls.data[split][nmb])
        except Exception:
            err_tabs.append(nmb)
    if err_tabs:
        print(f'\n\033[91mWARNING!\033[0m\n{dataset_name}-{split} '
              f'prepare_table has failed {len(err_tabs)} times on:', err_tabs[:20])

    return dataset_name, split, p_tabs, err_tabs


@pytest.fixture(scope="session", params=tabs, ids=id_func(tabs))
def prepare_tests(request):
    dataset_name, split = request.param
    cls = DATASET_CLASSES[dataset_name]()
    cls.load(split)
    return dataset_name, split, cls
