#!/usr/bin/env python3

import os
import requests
import json
import logging
import random
from .data import get_dataset_class_by_name

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def success():
    resp = jsonify(success=True)
    return resp

@app.route('/table', methods=['GET', 'POST'])
def render_table():
    dataset_name = request.args.get('dataset')
    dataset_split = request.args.get('split')
    table_idx = request.args.get('i')

    if dataset_name:
        app.config["dataset_name"] = dataset_name

    if dataset_split: 
        app.config["dataset_split"] = dataset_split

    if table_idx:
        app.config["table_idx"] = int(table_idx)

    return get_table_data()



@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info(f"Page loaded")

    return render_template('index.html',
        dataset=app.config["dataset_name"],
        datasets=list(app.config["dataset_paths"].keys()),
        table_idx=app.config["table_idx"]
    )


def load_dataset(dataset_name, split="dev"):
    logger.info(f"Loading {dataset_name}")
    dataset = get_dataset_class_by_name(dataset_name)()

    dataset_paths = app.config["dataset_paths"]
    dataset.load(splits=[split], path=dataset_paths[dataset_name])
    app.config["datasets"][dataset_name] = dataset

    return dataset



def get_dataset(dataset_name):
    dataset = app.config["datasets"].get(dataset_name)

    if not dataset:
        dataset = load_dataset(dataset)

    return dataset



def get_table_data(dataset_name=None, split=None, index=None):
    if not dataset_name:
        dataset_name = app.config["dataset_name"]

    if not split:
        split = app.config["dataset_split"]

    if not index:
        index = app.config["table_idx"]

    dataset = get_dataset(dataset_name)
    html = dataset.get_table_html(split=split, index=index)
    ref = dataset.get_reference(split=split, index=index)

    return {
        "html": html,
        "ref": ref
    }



def create_app(*args, **kwargs):
    random.seed(42)

    app.config["datasets"] = {}
    app.config["dataset_name"] = "scigen"
    app.config["dataset_split"] = "dev"
    app.config["table_idx"] = 0
    app.config["dataset_paths"] = {
        "totto" :  None,
        "hitab" : "/lnet/work/people/kasner/datasets/HiTab/data",
        "scigen" : "/lnet/work/people/kasner/datasets/SciGen/dataset"
    }

    load_dataset(app.config["dataset_name"])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)