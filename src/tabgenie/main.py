#!/usr/bin/env python3

import os
import json
import logging
from pkgutil import get_data
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

    if content.get("edited_cells"):
        content["edited_cells"] = json.loads(content["edited_cells"])

    pipeline_name = content["pipeline"]
    out = run_pipeline(pipeline_name, content, force=bool(content["edited_cells"]))

    return {"out": out}


@app.route("/table", methods=["GET", "POST"])
def render_table():
    dataset_name = request.args.get("dataset")
    split = request.args.get("split")
    table_idx = int(request.args.get("table_idx"))
    # pipelines = json.loads(request.args.get("pipelines"))

    table_data = get_table_data(dataset_name, split, table_idx)
    # table_data["pipeline_outputs"] = []

    # for pipeline, attrs in pipelines.items():
    #     if not attrs["active"]:
    #         continue

    #     content = {
    #         "dataset_obj" : get_dataset(dataset_name, split),
    #         "dataset": dataset_name,
    #         "table_idx": table_idx,
    #         "split": split,
    #     }
    #     out = run_pipeline(pipeline, content, cache_only=True)

    #     if out:
    #         table_data["pipeline_outputs"].append({
    #             "pipeline_name" : pipeline,
    #             "out": out
    #         })

    return table_data


@app.route('/export_to_file', methods=['GET', 'POST'])
def export_to_file():
    content = request.json
    export_option = content["export_option"]
    export_format = content["export_format"]
    export_examples = json.loads(content["export_examples"])
    # TODO export edited cells
    # edited_cells = json.loads(content.get("edited_cells") or {})

    export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, 'tmp')

    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)

    default_template = "export/json_templates/default.yml"

    os.makedirs(os.path.join(export_dir, "files"))
    file_to_download = export_examples_to_file(export_examples, export_dir=os.path.join(export_dir, "files"), export_format=export_format, json_template=default_template)

    if export_option == "favourites":
        file_to_download = os.path.join(export_dir, "export.zip")
        shutil.make_archive(file_to_download.rstrip(".zip"), 'zip', os.path.join(export_dir, "files"))

    logger.info("Sending file")
    return send_file(file_to_download,
                    mimetype='text/plain',
                    as_attachment=True)


def export_examples_to_file(examples_to_export, export_format, export_dir, export_filename=None, json_template=None):
    
    if type(examples_to_export) is dict:
        # TODO look at this in more detail, favourites behaves differently
        examples_to_export = examples_to_export.values()

    pipeline_args = {
        "examples_to_export" : examples_to_export,
        "export_format" : export_format,
        "json_template" : json_template,
        "dataset_objs" : {dataset_name : get_dataset(dataset_name, split) for dataset_name, split in map(lambda x: (x["dataset"], x["split"]), examples_to_export)}
    }
    os.makedirs(export_dir, exist_ok=True);
    exported = run_pipeline("export", pipeline_args, force=True)

    if export_format == "json":
        # only a single, aggregated output
        out_filename = export_filename or "out.json"

        with open(os.path.join(export_dir, out_filename), "w") as f:
            json.dump(exported, f, indent=4, ensure_ascii=False)
    else:
        # multiple outputs
        for e, exported_table in zip(examples_to_export, exported):
            out_filename = f"{e['dataset']}_{e['split']}_tab_{e['table_idx']}.{export_format}"

            if export_format == "xlsx":
                exported_table.to_excel(os.path.join(export_dir, out_filename), index=False, engine="xlsxwriter")
            else:
                with open(os.path.join(export_dir, out_filename), "w") as f:
                    f.write(exported_table)

    return os.path.join(export_dir, out_filename)



def export_dataset(dataset_name, split, out_dir, export_format, json_template=None):
    dataset = get_dataset(dataset_name, split)

    examples_to_export = [{
      "dataset": dataset_name,
      "split": split,
      "table_idx": table_idx
    } for table_idx in range(dataset.get_example_count(split))]

    # only relevant for JSON
    export_filename = f"{split}.json"

    export_examples_to_file(examples_to_export, export_format=export_format, export_dir=out_dir, export_filename=export_filename, json_template=json_template)
  
    logger.info("Export finished")

def initialize_dataset(dataset_name):
    # dataset_path = app.config["dataset_paths"][dataset_name]
    dataset_path = None # not needed for HF
    dataset = get_dataset_class_by_name(dataset_name)(path=dataset_path)
    app.config["datasets_obj"][dataset_name] = dataset

    return dataset


def initialize_pipeline(pipeline_name):
    pipeline_cfg = app.config["pipelines"][pipeline_name]

    if "config_template_file" in pipeline_cfg:
        with open(os.path.join(TEMPLATES_DIR, pipeline_cfg["config_template_file"])) as f:
            pipeline_cfg["config_template"] = f.read()

    pipeline_obj = get_pipeline_class_by_name(pipeline_cfg["class"])(cfg=pipeline_cfg)
    app.config["pipelines_obj"][pipeline_name] = pipeline_obj

    return pipeline_obj


def run_pipeline(pipeline_name, content, cache_only=False, force=False):
    pipeline = app.config["pipelines_obj"].get(pipeline_name)

    # if not pipeline:
    #     logger.info(f"Initializing {pipeline_name}")
    #     pipeline = initialize_pipeline(pipeline_name)

    if content.get("dataset") and content.get("split"):
        dataset_obj = get_dataset(dataset_name=content["dataset"], split=content["split"])
        content["dataset_obj"] = dataset_obj

    out = pipeline.run(content, cache_only=cache_only, force=force)

    return out


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
    prompt = dataset.get_prompt(app.config.get("default_prompt"))
    dataset_info = dataset.get_info()

    return {"html": html, "total_examples": dataset.get_example_count(split), "dataset_info" : dataset_info, "generated_outputs" : generated_outputs, "prompt" : prompt}



@app.route("/", methods=["GET", "POST"])
def index():
    logger.info(f"Page loaded")

    return render_template(
        "index.html",
        datasets=app.config["datasets"],
        pipelines=app.config["pipelines"],
        generated_outputs=app.config["generated_outputs"],
        default_dataset=app.config["default_dataset"],
        host_prefix=app.config["host_prefix"]
    )


def create_app():
    with open("config.yml") as f:
        config = yaml.safe_load(f)

    app.config.update(config)
    app.config["datasets_obj"] = {}
    app.config["pipelines_obj"] = {}

    for pipeline_name in app.config["pipelines"].keys():
        initialize_pipeline(pipeline_name)

    # preload
    if config["cache_dev_splits"]:
        for dataset_name in app.config["datasets"]:
            get_dataset(dataset_name, "dev")

    return app
