#!/usr/bin/env python3

from email.policy import default
import os
import requests
import json
import logging
from .data import get_dataset_class_by_name
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from .model import Model


app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def success():
    resp = jsonify(success=True)
    return resp


@app.route('/load_model', methods=['GET', 'POST'])
def load_model():
    model_name = request.args.get("model")

    logger.info(f"Loading model {model_name}")
    m = Model()
    m.load(
        exp_dir="/lnet/work/people/kasner/projects/ng-nlg/experiments",
        experiment=model_name
    )
    app.config["model"] = m
    return success()


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        content = request.json
        logger.info(f"Incoming content: {content}")
        m = app.config["model"]

        dataset_name = content["dataset"]
        split = content["split"]
        table_idx = content["table_idx"]
        cells = content["cells"]

        dataset = get_dataset(dataset_name, split)
        gen_input = dataset.get_generation_input(table_idx, cells)

        out = m.generate(gen_input)
        return {
            "out" : out
        }


@app.route('/table', methods=['GET', 'POST'])
def render_table():
    dataset_name = request.args.get('dataset')
    split = request.args.get('split')
    table_idx = int(request.args.get('table_idx'))

    return get_table_data(dataset_name, split, table_idx)


def initialize_dataset(dataset_name):
    dataset_path = app.config["dataset_paths"][dataset_name]
    dataset = get_dataset_class_by_name(dataset_name)(path=dataset_path)
    app.config["datasets"][dataset_name] = dataset

    return dataset


def get_dataset(dataset_name, split):
    dataset = app.config["datasets"].get(dataset_name)

    if not dataset:
        logger.info(f"Initializing {dataset_name}")
        dataset = initialize_dataset(dataset_name)

    if not dataset.has_split(split):
        logger.info(f"Loading {dataset_name} / {split}")
        dataset.load(split=split)

    return dataset


def get_table_data(dataset_name, split, index):
    dataset = get_dataset(dataset_name, split)
    html = dataset.get_table_html(split=split, index=index)
    ref = dataset.get_reference(split=split, index=index)

    return {
        "html": html,
        "ref": ref,
        "total_examples" : len(dataset.data[split])
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    logger.info(f"Page loaded")

    return render_template('index.html',
        datasets=list(app.config["dataset_paths"].keys()),
    )


def create_app(*args, **kwargs):
    app.config["datasets"] = {}
    app.config["dataset_paths"] = {
        "webnlg" :  None,
        "totto" :  None,
        "hitab" : "data/HiTab/data",
        "scigen" : "data/SciGen/dataset",
        "logicnlg" : "data/LogicNLG/data",
        "logic2text" : "data/Logic2Text/dataset"
    }
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)