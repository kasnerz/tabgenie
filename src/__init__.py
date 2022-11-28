#!/usr/bin/env python3

import os
import requests
import json
import logging
import argparse
from .loaders.data import get_dataset_class_by_name
from collections import defaultdict
from flask import Flask, render_template, jsonify, request
from .model import Model

app = Flask(__name__)

logging.basicConfig(
    format="%(levelname)s - %(message)s", level=logging.INFO, datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def success():
    resp = jsonify(success=True)
    return resp


@app.route("/load_model", methods=["GET", "POST"])
def load_model():
    model_name = request.args.get("model")

    logger.info(f"Loading model {model_name}")
    m = Model()
    m.load(exp_dir=app.config["exp_dir"], experiment=model_name)
    app.config["model"] = m
    return success()


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if request.method == "POST":
        content = request.json
        logger.info(f"Incoming content: {content}")
        m = app.config["model"]

        dataset_name = content["dataset"]
        split = content["split"]
        table_idx = content["table_idx"]
        cell_ids = content["cells"]

        dataset = get_dataset(dataset_name, split)
        gen_input = dataset.get_generation_input(
            split=split, table_idx=table_idx, cell_ids=cell_ids
        )

        logger.info(f"Input: {gen_input}")
        out = m.generate(gen_input)

        return {"out": out}


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))

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
        dataset.load(split=split, max_examples=app.config["max_examples_per_split"])

    return dataset


def get_table_data(dataset_name, split, index):
    dataset = get_dataset(dataset_name, split)
    html = dataset.get_table_html(split=split, index=index)
    ref = dataset.get_reference(split=split, index=index)
    dataset_info = dataset.get_info()

    return {"html": html, "ref": ref, "total_examples": len(dataset.data[split]), "dataset_info" : dataset_info}


@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    return render_template(
        "index.html",
        datasets=list(app.config["dataset_paths"].keys()),
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"],
        mode=app.config["mode"],
    )


def create_app(*args, **kwargs):
    with open("config.json") as f:
        config = json.load(f)

    app.config.update(config)
    # app.config.from_file("config.json", load=json.load)
    app.config["datasets"] = {}
    return app


if __name__ == "__main__":
    app.run()
