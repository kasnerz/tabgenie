#!/usr/bin/env python3

import os
import requests
import pyjson5 as json
import logging
import argparse
from .loaders.data import get_dataset_class_by_name
from .processing.processing import get_pipeline_class_by_name
from collections import defaultdict
from flask import Flask, render_template, jsonify, request, send_file


app = Flask(__name__)

logging.basicConfig(
    format="%(levelname)s - %(message)s", level=logging.INFO, datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


def success():
    resp = jsonify(success=True)
    return resp


@app.route("/pipeline", methods=["GET", "POST"])
def get_pipeline_output():
    content = request.json
    logger.info(f"Incoming content: {content}")

    pipeline_name = content["pipeline"]
    out = run_pipeline(pipeline_name, content)

    return {"out": out}


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))
    pipelines = json.loads(request.args.get("pipelines"))

    table_data = get_table_data(dataset_name, split, table_idx)
    table_data["pipeline_outputs"] = []

    for pipeline, attrs in pipelines.items():
        if not attrs["active"]:
            continue

        content = {
            "dataset_obj" : get_dataset(dataset_name, split),
            "dataset": dataset_name,
            "table_idx": table_idx,
            "split": split,
        }
        out = run_pipeline(pipeline, content, cache_only=True)

        if out:
            table_data["pipeline_outputs"].append({
                "pipeline_name" : pipeline,
                "out": out
            })

    return table_data


def initialize_dataset(dataset_name):
    # dataset_path = app.config["dataset_paths"][dataset_name]
    dataset_path = None # not needed for HF
    dataset = get_dataset_class_by_name(dataset_name)(path=dataset_path)
    app.config["datasets_obj"][dataset_name] = dataset

    return dataset



def initialize_pipeline(pipeline_name):
    cfg = app.config["pipeline_cfg"].get(pipeline_name) or {}
    
    pipeline = get_pipeline_class_by_name(pipeline_name)(cfg=cfg)
    app.config["pipelines_obj"][pipeline_name] = pipeline

    return pipeline


def get_pipeline(pipeline_name):
    pipeline = app.config["pipelines_obj"].get(pipeline_name)

    if not pipeline:
        logger.info(f"Initializing {pipeline_name}")
        pipeline = initialize_pipeline(pipeline_name)

    return pipeline


def get_dataset(dataset_name, split):
    dataset = app.config["datasets_obj"].get(dataset_name)

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


def run_pipeline(pipeline_name, content, cache_only=False):
    pipeline = get_pipeline(pipeline_name)
    dataset_obj = get_dataset(dataset_name=content["dataset"], split=content["split"])

    content["dataset_obj"] = dataset_obj
    out = pipeline.run(content, cache_only)
    return out


@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    pipelines = {
        pipeline : {"active" : 1, "auto" : 1}
        for pipeline in app.config["pipelines"]
    }

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        pipelines=pipelines,
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"]
    )


def create_app(*args, **kwargs):
    with open("config.json") as f:
        config = json.load(f)

    app.config.update(config)
    # app.config.from_file("config.json", load=json.load)
    app.config["datasets_obj"] = {}
    app.config["pipelines_obj"] = {}

    # preload
    if config["preload"]:
        for dataset_name in app.config["datasets"]:
            get_dataset(dataset_name, "dev")

    return app


if __name__ == "__main__":
    app.run()
