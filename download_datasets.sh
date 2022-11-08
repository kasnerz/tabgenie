#!/bin/bash

mkdir -p data

echo "Caching Huggingface datasets to ${HF_DATASETS_CACHE} (can be changed by setting the environment variable HF_DATASETS_CACHE)"
python -c 'import datasets; \
    datasets.load_dataset("gem", "totto"); \
    datasets.load_dataset("gem", "web_nlg_en"); \
    datasets.load_dataset("gem", "e2e_nlg");'

echo "Other datasets are work in progress and are not available for download yet. You can download the datasets manually from their respective repositories."