#!/usr/bin/env python3

import os
import requests
import json
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


# @app.route("/load_model", methods=["GET", "POST"])
# def load_model():
#     model_name = request.args.get("model")

#     logger.info(f"Loading model {model_name}")
#     m = Model()
#     m.load(exp_dir=app.config["exp_dir"], experiment=model_name)
#     app.config["model"] = m
#     return success()


# @app.route("/generate", methods=["GET", "POST"])
# def generate():
#     content = request.json
#     logger.info(f"Incoming content: {content}")
#     m = app.config["model"]

#     dataset_name = content["dataset"]
#     split = content["split"]
#     table_idx = content["table_idx"]
#     cell_ids = content["cells"]

#     dataset = get_dataset(dataset_name, split)
#     gen_input = dataset.get_generation_input(
#         split=split, table_idx=table_idx, cell_ids=cell_ids
#     )

#     logger.info(f"Input: {gen_input}")
#     out = m.generate(gen_input)

#     return {"out": out}


# @app.route('/export', methods=['GET', 'POST'])
# def export():
#     content = request.json
#     dataset_name = content["dataset"]
#     split = content["split"]
#     table_idx = content["table_idx"]

#     src_dir = os.path.dirname(os.path.abspath(__file__))
#     files_dir = os.path.join(src_dir, os.pardir, 'files')
#     os.makedirs(files_dir, exist_ok=True)

#     file_to_download = os.path.join(files_dir, "export.json")
#     dataset = get_dataset(dataset_name, split)
#     export_content = dataset.export(split, [table_idx], export_format="linearize")

#     with open(file_to_download, "w") as f:
#         json.dump(dict(export_content), f)

#     logger.info("Sending file")
#     return send_file(file_to_download,
#                     mimetype='text/json',
#                     download_name='export.json',
#                     as_attachment=True)

@app.route("/pipeline", methods=["GET", "POST"])
def run_pipeline():
    content = request.json
    logger.info(f"Incoming content: {content}")

    pipeline_name = content["pipeline"]
    pipeline = get_pipeline(pipeline_name)
    
    dataset = get_dataset(dataset_name=content["dataset"], split=content["split"])

    inp = {
        "dataset": dataset,
        "content" : content
    }
    out = pipeline.run(inp)

    return {"out": out}


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))
    # export_format = request.args.get("export_format")

    return get_table_data(dataset_name, split, table_idx)


def initialize_dataset(dataset_name):
    # dataset_path = app.config["dataset_paths"][dataset_name]
    dataset_path = None # not needed for HF
    dataset = get_dataset_class_by_name(dataset_name)(path=dataset_path)
    app.config["datasets_obj"][dataset_name] = dataset

    return dataset


def initialize_pipeline(pipeline_name):
    pipeline = get_pipeline_class_by_name(pipeline_name)()
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
    # export = dataset.export(split=split, table_idxs=[index], export_format=export_format)

    return {"html": html, "ref": ref, "total_examples": len(dataset.data[split]), "dataset_info" : dataset_info}


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
