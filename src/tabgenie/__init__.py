#!/usr/bin/env python3

from .loaders import DATASET_CLASSES


def load_dataset(dataset_name):
    try:
        dataset = DATASET_CLASSES[dataset_name]()
    except ValueError:
        print(f"Dataset {dataset_name} does not exist. Available datasets: {DATASET_CLASSES.keys()}")

    dataset.load()
    return dataset
