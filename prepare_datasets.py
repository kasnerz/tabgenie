#!/usr/bin/env python3

import datasets
import json
from src.loaders import data

with open("config.json") as f:
    config = json.load(f)
    datasets = config["datasets"]

for dataset_name in datasets:
    cls = data.get_dataset_class_by_name(dataset_name)

    for split in ["train", "dev", "test"]:
        print(dataset_name, split)
        dataset = cls(path=None).load(split=split)
