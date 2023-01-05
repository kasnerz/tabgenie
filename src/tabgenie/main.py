#!/usr/bin/env python3

import os
import json
import logging
import yaml
import shutil
from .loaders.data import get_dataset_class_by_name
from .processing.processing import get_pipeline_class_by_name
from flask import Flask, render_template, jsonify, request, send_file


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


app = Flask("tabgenie", template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)

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

    if content.get("editedCells"):
        content["editedCells"] = json.loads(content["editedCells"])

    pipeline_name = content["pipeline"]
    out = run_pipeline(pipeline_name, content, force=bool(content["editedCells"]))

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


@app.route('/export_table', methods=['GET', 'POST'])
def export_table():
    content = request.json
    dataset_name = content["dataset"]
    split = content["split"]
    table_idx = content["table_idx"]
    export_format = content["format"]
    export_option = content["export_option"]
    favourites = content["favourites"]
    edited_cells = json.loads(content.get("editedCells") or {})

    src_dir = os.path.dirname(os.path.abspath(__file__))
    export_dir = os.path.join(src_dir, os.pardir, os.pardir, 'tmp')

    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)

    os.makedirs(export_dir)
    os.makedirs(os.path.join(export_dir, "files"))

    examples_to_export = []
    if export_option == "favourites":
        favourites = json.loads(favourites)

        for val in favourites.values():
            examples_to_export.append((val["dataset"], val["split"], val["table_idx"]))
    else:
        examples_to_export.append((dataset_name, split, table_idx))

    for example in examples_to_export:
        dataset_name = example[0]
        split = example[1]
        table_idx = example[2]

        export_file = os.path.join(export_dir, "files", f"{dataset_name}-{split}-{table_idx}.{export_format}")
        dataset = get_dataset(dataset_name, split)
        table = dataset.get_table(split=split, table_idx=table_idx, edited_cells=edited_cells)

        dataset.export_table(table, export_format=export_format, to_file=export_file)

    if export_option == "favourites":
        file_to_download = os.path.join(export_dir, "export.zip")
        shutil.make_archive(file_to_download.rstrip(".zip"), 'zip', os.path.join(export_dir, "files"))
    else:
        file_to_download = export_file

    logger.info("Sending file")
    return send_file(file_to_download,
                    mimetype='text/plain',
                    as_attachment=True)


def export_dataset(dataset_name, split, out_file, template_file):
    with open(template_file) as f:
        template = yaml.safe_load(f)

    dataset_cfg = template["dataset"]
    table_cfg = template["table"]
    dataset_format = dataset_cfg["format"]

    if dataset_format == "json":
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        dataset = get_dataset(dataset_name, split)
        exported = dataset.export(split, table_cfg)

        with open(out_file, "w") as f:
            json.dump({dataset_cfg["table_key"] : exported}, f, indent=4, ensure_ascii=False)
    else:
        raise NotImplementedError(f"Format '{dataset_format}' is not supported")


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

def run_pipeline(pipeline_name, content, cache_only=False, force=False):
    pipeline = get_pipeline(pipeline_name)
    dataset_obj = get_dataset(dataset_name=content["dataset"], split=content["split"])

    content["dataset_obj"] = dataset_obj
    out = pipeline.run(content, cache_only=cache_only, force=force)
    return out


def get_pipeline(pipeline_name):
    pipeline = app.config["pipelines_obj"].get(pipeline_name)

    if not pipeline:
        logger.info(f"Initializing {pipeline_name}")
        pipeline = initialize_pipeline(pipeline_name)

    return pipeline


def get_dataset(dataset_name, split):
    dataset = app.config["datasets_obj"].get(dataset_name)
    max_examples = app.config.get("max_examples_per_split", None)
    if max_examples is not None and max_examples < 1:
        max_examples = None

    if not dataset:
        logger.info(f"Initializing {dataset_name}")
        dataset = initialize_dataset(dataset_name)

    if not dataset.has_split(split):
        logger.info(f"Loading {dataset_name} / {split}")
        dataset.load(split=split, max_examples=max_examples)

        for name in app.config["generated_outputs"]:
            dataset.load_outputs(split=split, name=name)

    return dataset


def get_table_data(dataset_name, split, table_idx):
    dataset = get_dataset(dataset_name=dataset_name, split=split)
    table = dataset.get_table(split=split, table_idx=table_idx)
    html = dataset.export_table(table=table, export_format="html")
    generated_outputs = dataset.get_generated_outputs(table=table)
    dataset_info = dataset.get_info()

    return {"html": html, "total_examples": len(dataset.data[split]), "dataset_info" : dataset_info, "generated_outputs" : generated_outputs}



@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    pipelines = {
        pipeline : {"active" : 1, "auto" : 1}
        for pipeline in app.config["pipelines"]
    }

    generated_outputs = {
        generated_output : {"active" : 1}
        for generated_output in app.config["generated_outputs"]
    }

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        pipelines=pipelines,
        generated_outputs=generated_outputs,
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"]
    )


def create_app():
    with open("config.yml") as f:
        config = yaml.safe_load(f)

    app.config.update(config)
    app.config["datasets_obj"] = {}
    app.config["pipelines_obj"] = {}

    # preload
    if config["cache_dev_splits"]:
        for dataset_name in app.config["datasets"]:
            get_dataset(dataset_name, "dev")

    return app
