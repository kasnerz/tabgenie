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


def pytest_addoption(parser):
    parser.addoption("--num-examples", action="store", default=None, help="Number of examples for testing")


@pytest.fixture(scope="session")
def num_examples(request):
    num_examples = request.config.getoption("--num-examples")
    if num_examples is None:
        return None
    else:
        return int(num_examples)


def id_func(data):
    return [f'{key}-{spl}' for key, spl in data]


@pytest.fixture(scope="session", params=tabs, ids=id_func(tabs))
def prepare_split(request, num_examples):
    dataset_name, split = request.param
    cls = DATASET_CLASSES[dataset_name]()
    cls.load(split)
    data = cls.data[split]

    if num_examples is None:
        num_of_tbl = len(data)
    else:
        num_of_tbl = num_examples

    p_tabs = [None] * num_of_tbl
    err_tabs = []

    for nmb in range(num_of_tbl):
        try:
            p_tabs[nmb] = cls.prepare_table(data[nmb])
        except Exception:
            err_tabs.append(nmb)

    if err_tabs:
        print(f'\n\033[91mWARNING!\033[0m\n{dataset_name}-{split} '
              f'prepare_table has failed {len(err_tabs)} times on: {err_tabs[:20]}')

    return dataset_name, split, p_tabs


@pytest.fixture(scope="session", params=tabs, ids=id_func(tabs))
def prepare_tests(request, num_examples):
    dataset_name, split = request.param
    cls = DATASET_CLASSES[dataset_name]()
    cls.load(split)
    data = cls.data[split]

    if num_examples is None:
        num_of_tbl = len(data)
    else:
        num_of_tbl = num_examples

    return dataset_name, split, cls, num_of_tbl
