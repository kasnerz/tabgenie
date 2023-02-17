#!/usr/bin/env python3

from .loaders import DATASET_CLASSES

# ====================================
# methods provided for other packages
# usage: `from tabgenie import xyz`
# ====================================


def load_dataset(dataset_name, splits=None):
    try:
        dataset = DATASET_CLASSES[dataset_name]()
    except ValueError:
        print(f"Dataset {dataset_name} does not exist. Available datasets: {DATASET_CLASSES.keys()}")

    if splits:
        for split in splits:
            dataset.load(split)
    else:
        dataset.load()

    return dataset
